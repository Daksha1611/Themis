"""The arq review job. M1 posts a single placeholder comment."""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from arq import Retry

from app.github.auth import get_installation_token
from app.github.comments import GitHubRetryableError, post_review_comment
from app.observability.tracing import end_span, end_trace, start_span, start_trace
from app.schemas import ReviewJob
from app.storage.repository import create_run

logger = logging.getLogger(__name__)

DUMMY_COMMENT = "⚖️ Themis is reviewing this PR."


async def handle_review_job(ctx: dict[str, Any], job: dict[str, Any]) -> str:
    review_job = ReviewJob.model_validate(job)
    metadata = {
        "repo": review_job.repo_full_name,
        "pr_number": review_job.pr_number,
        "head_sha": review_job.head_sha,
        "installation_id": review_job.installation_id,
    }
    logger.info("Picked up review job %s", metadata)
    started_at = datetime.now(UTC)
    trace = start_trace("review.job", metadata)
    span = None

    try:
        span = start_span(trace, "github.installation_token", metadata)
        token = await get_installation_token(review_job.installation_id)
        end_span(span, {"ok": True})

        span = start_span(trace, "github.post_comment", {"body": DUMMY_COMMENT})
        await post_review_comment(
            token, review_job.repo_full_name, review_job.pr_number, DUMMY_COMMENT
        )
        end_span(span, {"posted": True})
        logger.info(
            "Posted dummy comment on %s#%s", review_job.repo_full_name, review_job.pr_number
        )

        span = start_span(trace, "storage.create_run", metadata)
        async with ctx["session_factory"]() as session:
            run = await create_run(
                session,
                {
                    "repo": review_job.repo_full_name,
                    "pr_number": review_job.pr_number,
                    "head_sha": review_job.head_sha,
                    "status": "dummy",
                    "started_at": started_at,
                    "completed_at": datetime.now(UTC),
                    "cost_usd": Decimal(0),
                },
            )
        end_span(span, {"run_id": str(run.id)})
        span = None
    except GitHubRetryableError as exc:
        logger.warning("Review job %s rate limited; retrying in %ss", metadata, exc.retry_after)
        end_span(span, None, error=exc)
        end_trace(trace, {"status": "retrying"}, error=exc)
        raise Retry(defer=exc.retry_after) from exc
    except Exception as exc:
        logger.exception("Review job failed %s", metadata)
        end_span(span, None, error=exc)
        end_trace(trace, {"status": "failed"}, error=exc)
        raise

    end_trace(trace, {"status": "dummy_complete", "run_id": str(run.id)})
    return "dummy_complete"
