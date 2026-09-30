"""The arq review job: auth → diff → baseline review → post → store."""

import logging
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from arq import Retry

from app.config import get_settings
from app.github.auth import get_installation_token
from app.github.client import GitHubRetryableError
from app.github.comments import post_findings, post_review_comment
from app.github.diff import fetch_pr_diff
from app.graph.baseline import BaselineResult, run_baseline_review
from app.observability.tracing import observe, trace_attributes, update
from app.schemas import LLMConfig, PRRef, ReviewJob, ReviewResult, TokenUsage
from app.storage.repository import create_run

logger = logging.getLogger(__name__)

NO_ISSUES_COMMENT = "⚖️ Themis found no logic bugs or security issues in this diff."
ERROR_COMMENT = "⚖️ Themis encountered an error during review. This run has been logged."

Status = Literal["success", "partial", "failed"]


class _Run:
    """What the job learns as it goes; becomes the review_runs row and the trace output."""

    def __init__(self, job: ReviewJob) -> None:
        self.job = job
        self.started_at = datetime.now(UTC)
        self.t0 = time.monotonic()
        self.diff_chars: int | None = None
        self.diff_truncated = False
        self.baseline: BaselineResult | None = None
        self.error: str | None = None
        self.run_id = ""

    def row(self, status: Status) -> dict[str, Any]:
        llm = self.baseline.llm_response if self.baseline else None
        findings = self.baseline.findings if self.baseline else []
        return {
            "repo": self.job.repo_full_name,
            "pr_number": self.job.pr_number,
            "head_sha": self.job.head_sha,
            "status": status,
            "started_at": self.started_at,
            "completed_at": datetime.now(UTC),
            "cost_usd": Decimal(str(llm.cost_usd)) if llm else Decimal(0),
            "error": self.error,
            "finding_count": len(findings),
            "raw_finding_count": len(findings),
            "prompt_tokens": llm.prompt_tokens if llm else None,
            "completion_tokens": llm.completion_tokens if llm else None,
            "model": llm.model if llm else None,
            "diff_chars": self.diff_chars,
            "diff_truncated": self.diff_truncated,
        }

    def result(self, status: Status) -> ReviewResult:
        settings = get_settings()
        llm = self.baseline.llm_response if self.baseline else None
        findings = self.baseline.findings if self.baseline else []
        return ReviewResult(
            run_id=self.run_id,
            pr_ref=PRRef(
                repo=self.job.repo_full_name, number=self.job.pr_number, head_sha=self.job.head_sha
            ),
            findings=findings,
            raw_finding_count=len(findings),
            filtered_finding_count=len(findings),
            llm_config=LLMConfig(
                model=llm.model if llm else settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            ),
            token_usage=TokenUsage(
                prompt_tokens=llm.prompt_tokens if llm else 0,
                completion_tokens=llm.completion_tokens if llm else 0,
                total_tokens=llm.total_tokens if llm else 0,
            ),
            cost_usd=llm.cost_usd if llm else 0.0,
            latency_ms=int((time.monotonic() - self.t0) * 1000),
            guardrail_triggered=False,
            status=status,
            error=self.error,
        )


async def handle_review_job(ctx: dict[str, Any], job: dict[str, Any]) -> str:
    review_job = ReviewJob.model_validate(job)
    run = _Run(review_job)
    pr = f"{review_job.repo_full_name}#{review_job.pr_number}"
    trace_input = {
        "repo": review_job.repo_full_name,
        "pr_number": review_job.pr_number,
        "pr_title": review_job.pr_title,
        "head_sha": review_job.head_sha,
    }
    logger.info("Picked up review job %s", trace_input)

    # One trace per review; all reviews of the same PR share a session.
    with (
        trace_attributes(
            session_id=pr,
            tags=["baseline"],
            metadata={"repo": review_job.repo_full_name, "pr_number": str(review_job.pr_number)},
        ),
        observe(
            "review.job",
            input=trace_input,
            metadata={"installation_id": review_job.installation_id},
        ) as root,
    ):
        try:
            status = await _review(ctx, run)
        except GitHubRetryableError as exc:
            logger.warning("Review of %s rate limited; retrying in %ss", pr, exc.retry_after)
            update(root, output={"status": "retrying"})
            raise Retry(defer=exc.retry_after) from exc
        except Exception:
            logger.exception("Review job failed %s", trace_input)
            raise
        update(root, output=run.result(status).model_dump(mode="json"))
        if status == "failed":
            # Make failed reviews filterable by level in Langfuse, not just by reading the output.
            update(root, level="ERROR", status_message=(run.error or "review failed")[:500])
        elif status == "partial":
            update(root, level="WARNING", status_message="some findings failed validation")
    return status


async def _review(ctx: dict[str, Any], run: _Run) -> Status:
    job = run.job
    try:
        with observe("github.auth", input={"installation_id": job.installation_id}) as span:
            token = await get_installation_token(job.installation_id)
            update(span, output={"ok": True})
    except GitHubRetryableError:
        raise
    except Exception as exc:
        # Without a token Themis cannot post the error comment; record the run and let arq log it.
        run.error = f"GitHub auth failed: {exc!r}"
        await _store(ctx, run, "failed")
        raise

    try:
        with observe(
            "github.fetch_diff", input={"repo": job.repo_full_name, "pr_number": job.pr_number}
        ) as span:
            diff = await fetch_pr_diff(token, job.repo_full_name, job.pr_number)
            update(span, output={"diff_chars": diff.original_chars, "truncated": diff.truncated})
    except GitHubRetryableError:
        raise
    except Exception as exc:
        logger.exception("Diff fetch failed for %s#%s", job.repo_full_name, job.pr_number)
        return await _fail(ctx, run, token, f"diff fetch failed: {exc!r}")
    run.diff_chars, run.diff_truncated = diff.original_chars, diff.truncated

    with observe(
        "baseline.review", input={"diff_chars": len(diff.text), "truncated": diff.truncated}
    ) as span:
        baseline = await run_baseline_review(
            diff.text, {"pr_title": job.pr_title, "repo_full_name": job.repo_full_name}
        )
        llm = baseline.llm_response
        output: dict[str, Any] = {
            "status": baseline.status,
            "finding_count": len(baseline.findings),
            "parse_error_count": len(baseline.parse_errors),
            "prompt_tokens": llm.prompt_tokens if llm else 0,
            "completion_tokens": llm.completion_tokens if llm else 0,
            "cost_usd": llm.cost_usd if llm else 0.0,
        }
        if baseline.parse_errors:
            output["parse_errors"] = baseline.parse_errors
            if llm is not None:
                output["raw_response"] = llm.content
        update(span, output=output)
        if baseline.status == "failed":
            update(span, level="ERROR", status_message="; ".join(baseline.parse_errors)[:500])
    run.baseline = baseline

    if baseline.status == "failed":
        return await _fail(
            ctx, run, token, "baseline review failed: " + "; ".join(baseline.parse_errors)
        )

    with observe("github.post_comments", input={"finding_count": len(baseline.findings)}) as span:
        try:
            if baseline.findings:
                posted = await post_findings(
                    token,
                    job.repo_full_name,
                    job.pr_number,
                    job.head_sha,
                    baseline.findings,
                    diff.text,
                )
                update(span, output={**posted.model_dump(), "rate_limited": False})
            else:
                await post_review_comment(
                    token, job.repo_full_name, job.pr_number, NO_ISSUES_COMMENT
                )
                update(
                    span,
                    output={"line_comments": 0, "no_issues_comment": True, "rate_limited": False},
                )
        except GitHubRetryableError:
            update(span, output={"rate_limited": True})
            raise
        except Exception as exc:
            logger.exception("Posting findings failed for %s#%s", job.repo_full_name, job.pr_number)
            run.error = f"posting findings failed: {exc!r}"
            await _store(ctx, run, "failed")
            return "failed"

    status: Status = "partial" if baseline.status == "partial" else "success"
    await _store(ctx, run, status)
    return status


async def _fail(ctx: dict[str, Any], run: _Run, token: str, error: str) -> Status:
    """Tell the PR the run failed, record it, and finish without an arq retry."""
    run.error = error
    job = run.job
    try:
        with observe("github.post_comments", input={"error_comment": True}) as span:
            await post_review_comment(token, job.repo_full_name, job.pr_number, ERROR_COMMENT)
            update(span, output={"error_comment_posted": True})
    except Exception:
        logger.exception(
            "Could not post the error comment on %s#%s", job.repo_full_name, job.pr_number
        )
    await _store(ctx, run, "failed")
    return "failed"


async def _store(ctx: dict[str, Any], run: _Run, status: Status) -> None:
    with observe("storage.write", input={"status": status}) as span:
        async with ctx["session_factory"]() as session:
            record = await create_run(session, run.row(status))
        run.run_id = str(record.id)
        update(span, output={"run_id": run.run_id})
