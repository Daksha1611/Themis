"""Eval runner (M3 Step 5): replay a benchmark split through the real review path.

    python -m evals.runner --split dev [--limit N] [--resume] [--no-cache] [--cache-only]
                           [--dry-run] [--i-know-this-is-holdout]

Calls the same `run_baseline_review` the worker calls, with one pinned provider and model and the
cascade disabled (ADR-024). Scored cases: kept buggy cases (dropped ones are skipped, no LLM calls)
and all clean cases. Results are written per case to evals/results/<run_id>/results.jsonl as they
complete, so an interrupted run resumes with --resume; summary.json is written at the end.

Exit codes: 0 done, 2 refused (holdout guard, or the dry run says the run does not fit),
3 stopped early (rate-limit budget exhausted; resume later), 4 cache-only miss.
"""

import argparse
import asyncio
import hashlib
import json
import random
import re
import subprocess
import sys
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.graph.baseline import BaselineResult, build_messages, run_baseline_review
from app.llm import PinnedLLM
from evals.benchmark.label import DATA, LABELS, load_labels
from evals.cache import DEFAULT_PATH, ResponseCache

RESULTS = Path("evals/results")
# Run order is shuffled with a recorded seed so a day boundary (Q64: the daily budget splits the
# run) cannot line up with a repo, category or buggy/clean grouping.
ORDER_SEED = 20261003
CACHE_PATH = DEFAULT_PATH
# Every eval case gets the same neutral title. The real commit subject ("Fix X") would tell the
# reviewer what the bug is, and buggy and clean cases would be told apart by their titles.
EVAL_PR_TITLE = "Proposed change"

# Groq free tier for openai/gpt-oss-120b (docs/vault/09 External Facts.md, verified 2026-10-02).
TOKENS_PER_MINUTE = 8_000  # also the hard per-request ceiling: one request cannot exceed it
TOKENS_PER_DAY = 200_000
REQUESTS_PER_DAY = 1_000
MAX_RATE_RETRIES = 6  # per-minute 429s in a row before the run checkpoints and stops
MAX_ERROR_RETRIES = 2  # 5xx and connection errors before a case is recorded as failed
TOKENIZER_NOTE = (
    "LiteLLM token_counter: tiktoken cl100k_base (a local estimate; gpt-oss uses its own "
    "tokenizer, so actual counts differ somewhat)"
)

DAILY_LIMIT = re.compile(r"per day|\bTPD\b|\bRPD\b", re.IGNORECASE)
TOO_LARGE = re.compile(
    r"too large|context.length|maximum context|reduce the length|context_length_exceeded",
    re.IGNORECASE,
)
RETRY_IN = re.compile(r"try again in (?:(\d+)m)?([\d.]+)(ms|s)", re.IGNORECASE)


# Diff transform applied to every case before review (owner decision, 2026-10-04): in removed
# lines, issue/PR numbers and GitHub issue/PR links are masked; the comment text is kept. This
# removes the memorisation route (the model may know what upstream issue #N was about) while
# keeping the realistic signal. Versioned: the name is recorded in run.json.
DIFF_TRANSFORM = "mask-issue-refs-v1"
ISSUE_LINK = re.compile(r"https?://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/\d+[\w/#.-]*")
ISSUE_NUMBER = re.compile(r"(?<![\w&])#\d+\b")


def mask_issue_refs(diff: str) -> str:
    """Mask issue references in the removed (-) lines only; everything else is unchanged."""
    out = []
    for line in diff.split("\n"):
        if line.startswith("-") and not line.startswith("---"):
            line = ISSUE_NUMBER.sub("#N", ISSUE_LINK.sub("<issue-link>", line))
        out.append(line)
    return "\n".join(out)


# The run fingerprint (owner decision, 2026-10-04): two hashes recorded in run.json and checked
# by --resume. The code hash covers the modules the review path imports, plus the diff
# transform; the prompt hash covers the rendered prompts of the full scored set, catching
# eval-side changes (neutral title, masking, case data, labels) outside those modules.
REVIEW_PATH_MODULES = (
    "app/config.py",
    "app/github/client.py",
    "app/github/diff.py",
    "app/graph/baseline.py",
    "app/llm.py",
    "app/observability/tracing.py",
    "app/schemas.py",
    "app/taxonomy.py",
)


def file_hashes(read: Callable[[str], bytes] = lambda p: Path(p).read_bytes()) -> dict[str, str]:
    return {path: hashlib.sha256(read(path)).hexdigest() for path in REVIEW_PATH_MODULES}


def code_hash(files: dict[str, str], transform: str = "") -> str:
    payload = "\n".join(f"{path} {digest}" for path, digest in sorted(files.items()))
    return hashlib.sha256(
        f"{payload}\ntransform {transform or DIFF_TRANSFORM}".encode()
    ).hexdigest()


def rendered_prompt(case: dict[str, Any]) -> list[dict[str, str]]:
    """The prompt a case is reviewed with: the same path as --dry-run and run_case."""
    return build_messages(mask_issue_refs(case["diff"]), eval_metadata(case))


def prompt_hash(cases: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for case in sorted(cases, key=lambda c: c["case_id"]):
        rendered = json.dumps(rendered_prompt(case), sort_keys=True, ensure_ascii=False)
        digest.update(
            f"{case['case_id']} {hashlib.sha256(rendered.encode()).hexdigest()}\n".encode()
        )
    return digest.hexdigest()


def fingerprint(cases: list[dict[str, Any]]) -> dict[str, Any]:
    files = file_hashes()
    return {
        "code_hash": code_hash(files),
        "code_files": files,
        "prompt_hash": prompt_hash(cases),
        "diff_transform": DIFF_TRANSFORM,
    }


def fingerprint_mismatch(recorded: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Human-readable reasons the current code or prompts differ from a run's record."""
    problems = []
    if recorded["code_hash"] != current["code_hash"]:
        changed = [
            p
            for p in sorted(set(recorded["code_files"]) | set(current["code_files"]))
            if recorded["code_files"].get(p) != current["code_files"].get(p)
        ]
        problems.append(
            "code hash changed"
            + (f" (files: {', '.join(changed)})" if changed else " (diff transform)")
        )
    if recorded["prompt_hash"] != current["prompt_hash"]:
        problems.append("prompt hash changed (rendered prompts of the scored set differ)")
    return problems


class BudgetExhausted(Exception):
    """The pinned model's rate-limit budget is spent; checkpoint and resume later."""


class CacheOnlyMiss(Exception):
    """A --cache-only run needed a provider call."""


def eval_metadata(case: dict[str, Any]) -> dict[str, Any]:
    return {"pr_title": EVAL_PR_TITLE, "repo_full_name": case["repo"]}


def scored_cases(split: str, labels: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Kept buggy cases plus all clean cases, by case ID. Dropped buggy cases are skipped;
    unlabelled buggy cases (holdout before it is labelled) are kept."""
    cases = [json.loads(line) for line in (DATA / f"{split}.jsonl").read_text().splitlines()]
    return sorted(
        (
            c
            for c in cases
            if c["kind"] == "clean" or labels.get(c["case_id"], {}).get("valid", True) is True
        ),
        key=lambda c: c["case_id"],
    )


def run_order(cases: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """Cases in a reproducible shuffled order (sorted by case ID first, then shuffled)."""
    ordered = sorted(cases, key=lambda c: c["case_id"])
    random.Random(seed).shuffle(ordered)  # noqa: S311 (reproducible order, not security)
    return ordered


def estimate_tokens(messages: list[dict[str, str]]) -> int:
    import litellm  # noqa: PLC0415 (heavy import; app.llm configures it first)

    return int(litellm.token_counter(model="gpt-4o", messages=messages))


COMPLETION_TOKENS_PER_CASE = 718  # mean measured in dev baseline v1 (2026-10-03)


def dry_run(
    cases: list[dict[str, Any]],
    max_tokens: int,
    out: Callable[[str], None] = print,
    extra: dict[str, int] | None = None,
) -> bool:
    """Build every prompt and report token estimates without calling anything. True if every
    request fits the per-request ceiling and the whole run fits one day's token budget even if
    every response used its full max_tokens."""
    rows = []
    for case in cases:
        prompt = estimate_tokens(build_messages(mask_issue_refs(case["diff"]), eval_metadata(case)))
        prompt += (extra or {}).get(case["case_id"], 0)
        rows.append((case["case_id"], case["kind"], prompt, prompt + max_tokens))
    out(f"Token estimates per case ({TOKENIZER_NOTE}); request = prompt + max_tokens {max_tokens}")
    out("case_id           kind   prompt  request")
    for cid, kind, prompt, request in rows:
        out(f"{cid}  {kind:<5}  {prompt:>6}  {request:>7}")
    prompts = [r[2] for r in rows]
    largest = max(r[3] for r in rows) if rows else 0
    over = [r[0] for r in rows if r[3] > TOKENS_PER_MINUTE]
    prompt_total = sum(prompts)
    worst_total = prompt_total + max_tokens * len(rows)
    out("")
    out(f"cases: {len(rows)}")
    out(f"prompt tokens: max {max(prompts, default=0)}, total {prompt_total}")
    out(f"largest request: {largest} (per-request ceiling {TOKENS_PER_MINUTE}; over it: {over})")
    out(
        f"daily budget {TOKENS_PER_DAY} tokens, {REQUESTS_PER_DAY} requests: prompts alone "
        f"{prompt_total} ({prompt_total / TOKENS_PER_DAY:.0%}); worst case with full "
        f"max_tokens {worst_total} ({worst_total / TOKENS_PER_DAY:.0%}); "
        f"requests {len(rows)}"
    )
    expected = prompt_total + COMPLETION_TOKENS_PER_CASE * len(rows)
    out(
        f"expected total with v1's mean {COMPLETION_TOKENS_PER_CASE} completion tokens per case: "
        f"{expected} = {expected / TOKENS_PER_DAY:.2f} days of Groq quota"
    )
    fits_request = not over
    fits_day = worst_total <= TOKENS_PER_DAY and len(rows) <= REQUESTS_PER_DAY
    out(f"every request fits: {fits_request}; run fits one day's budget: {fits_day}")
    if not fits_day and prompt_total <= TOKENS_PER_DAY:
        spare = (TOKENS_PER_DAY - prompt_total) / max(len(rows), 1)
        out(
            f"the run fits one day only if responses average <= {spare:.0f} completion tokens "
            "(unknown before calling)"
        )
    return fits_request and fits_day


@dataclass
class TokenWindow:
    """Keeps the estimated tokens sent in any 60 seconds under the per-minute limit."""

    limit: int = TOKENS_PER_MINUTE
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
    sent: deque[tuple[float, int]] = field(default_factory=deque)

    async def reserve(self, tokens: int) -> None:
        while True:
            now = self.clock()
            while self.sent and now - self.sent[0][0] >= 60:
                self.sent.popleft()
            if not self.sent or sum(t for _, t in self.sent) + tokens <= self.limit:
                self.sent.append((now, tokens))
                return
            await self.sleep(60 - (now - self.sent[0][0]) + 0.1)


def classify(result: BaselineResult) -> str:
    """success | partial | failed:parse | failed:provider-limit | failed:provider-error |
    retry:rate-minute | stop:rate-day | retry:error | stop:cache-miss"""
    if result.status in ("success", "partial"):
        return result.status
    if result.error_type is None:
        return "failed:parse"  # the model answered, but not with a JSON array
    if result.error_type == "CacheMiss":
        return "stop:cache-miss"
    status, detail = result.error_status, result.error_detail
    if status == 429:
        return "stop:rate-day" if DAILY_LIMIT.search(detail) else "retry:rate-minute"
    if status == 413 or TOO_LARGE.search(detail):
        return "failed:provider-limit"
    if status is None or status >= 500:
        return "retry:error"
    return "failed:provider-error"


def backoff_seconds(detail: str, attempt: int) -> float:
    """The provider's own 'try again in …' hint when present, else exponential from 2 s."""
    if match := RETRY_IN.search(detail):
        minutes, value, unit = match.groups()
        seconds = float(value) / (1000 if unit.lower() == "ms" else 1)
        return seconds + 60 * int(minutes or 0) + 0.5
    return float(2 ** (attempt + 1))


Review = Callable[[str, dict[str, Any], PinnedLLM], Awaitable[BaselineResult]]


@dataclass
class Runner:
    pinned: PinnedLLM
    cache: ResponseCache | None
    max_tokens: int
    temperature: float
    window: TokenWindow = field(default_factory=TokenWindow)
    review: Review = run_baseline_review
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
    provider_calls: int = 0

    async def run_case(self, case: dict[str, Any]) -> dict[str, Any]:
        diff = mask_issue_refs(case["diff"])
        messages = build_messages(diff, eval_metadata(case))
        estimate = estimate_tokens(messages)
        key = (
            self.cache.key(
                self.pinned.provider, self.pinned.model, messages, self.temperature, self.max_tokens
            )
            if self.cache
            else ""
        )
        cached = bool(self.cache and self.cache.contains(key))
        if self.cache is not None and self.cache.cache_only and not cached:
            raise CacheOnlyMiss(case["case_id"])
        attempts = rate_retries = error_retries = 0
        while True:
            if not cached:
                await self.window.reserve(estimate + self.max_tokens)
                attempts += 1
                self.provider_calls += 1
            started = time.monotonic()
            result = await self.review(diff, eval_metadata(case), self.pinned)
            elapsed_ms = round((time.monotonic() - started) * 1000)
            outcome = classify(result)
            if outcome == "stop:cache-miss":
                raise CacheOnlyMiss(case["case_id"])
            if outcome == "stop:rate-day":
                raise BudgetExhausted(result.error_detail[:300])
            if outcome == "retry:rate-minute":
                rate_retries += 1
                if rate_retries > MAX_RATE_RETRIES:
                    raise BudgetExhausted(f"rate-limited {rate_retries} times in a row")
                await self.sleep(backoff_seconds(result.error_detail, rate_retries))
                continue
            if outcome == "retry:error":
                error_retries += 1
                if error_retries <= MAX_ERROR_RETRIES:
                    await self.sleep(backoff_seconds("", error_retries))
                    continue
                outcome = "failed:provider-error"
            break
        latency_ms = elapsed_ms
        if self.cache and result.llm_response is not None:
            if cached:
                latency_ms = self.cache.latency(key) or elapsed_ms
            else:
                self.cache.set_latency(key, elapsed_ms)
        response = result.llm_response
        return {
            "case_id": case["case_id"],
            "kind": case["kind"],
            "repo": case["repo"],
            "status": outcome,
            "findings": [f.model_dump() for f in result.findings],
            "parse_errors": result.parse_errors,
            "validation_retries": result.retries,
            "invalid_line": result.invalid_line,
            "error": {
                "type": result.error_type,
                "status": result.error_status,
                "detail": result.error_detail[:500],
            }
            if result.error_type
            else None,
            "pinned_provider": self.pinned.provider,
            "pinned_model": self.pinned.model,
            "provider": response.provider if response else None,
            "model": response.model if response else None,
            "prompt_tokens": response.prompt_tokens if response else 0,
            "completion_tokens": response.completion_tokens if response else 0,
            "estimated_prompt_tokens": estimate,
            "cost_usd_estimate": response.cost_usd if response else 0.0,
            "latency_ms": latency_ms if response else None,
            "cached": cached,
            "diff_masked": diff != case["diff"],
            "provider_attempts": attempts,
        }


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def git_state() -> tuple[str, bool]:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "app", "evals"], text=True, capture_output=True
    )
    return sha.stdout.strip(), bool(dirty.stdout.strip())


def latest_open_run(split: str) -> Path | None:
    runs = sorted(
        (p for p in RESULTS.glob(f"{split}-*") if p.is_dir()),
        key=lambda p: json.loads((p / "run.json").read_text())["started_at"],
    )
    open_runs = [p for p in runs if not (p / "summary.json").exists()]
    return open_runs[-1] if open_runs else None


def done_ids(run_dir: Path) -> set[str]:
    path = run_dir / "results.jsonl"
    if not path.exists():
        return set()
    return {json.loads(line)["case_id"] for line in path.read_text().splitlines() if line.strip()}


HOLDOUT_WARNING = """
################################################################################
#  HOLDOUT SPLIT. The holdout is run only at milestones, after prompt tuning is  #
#  frozen. Running it now leaks it into tuning decisions (ADR-007).              #
#  Pass --i-know-this-is-holdout to confirm.                                     #
################################################################################
"""


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=("dev", "holdout"), required=True)
    parser.add_argument("--limit", type=int, help="only the first N scored cases (smoke runs)")
    parser.add_argument("--resume", action="store_true", help="continue the latest open run")
    cache_mode = parser.add_mutually_exclusive_group()
    cache_mode.add_argument("--no-cache", action="store_true", help="neither read nor write")
    cache_mode.add_argument("--cache-only", action="store_true", help="fail on any cache miss")
    parser.add_argument("--dry-run", action="store_true", help="estimate tokens; call nothing")
    parser.add_argument(
        "--context-budget",
        type=int,
        help="with --dry-run: add each case's retrieved-context block at this token budget",
    )
    parser.add_argument("--i-know-this-is-holdout", action="store_true")
    parser.add_argument(
        "--check-fingerprint",
        action="store_true",
        help="compare the latest open run's recorded fingerprint with the current code; no calls",
    )
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    if args.split == "holdout":
        print(HOLDOUT_WARNING, file=sys.stderr)
        if not args.i_know_this_is_holdout:
            print("Refusing: pass --i-know-this-is-holdout.", file=sys.stderr)
            return 2
    settings = get_settings()
    labels = load_labels(LABELS)
    cases = run_order(scored_cases(args.split, labels), ORDER_SEED)[: args.limit]
    if args.dry_run:
        extra = None
        if args.context_budget:
            from evals.context_eval import context_block_tokens  # noqa: PLC0415 (heavy)

            extra = context_block_tokens(cases, args.context_budget)
            print(f"context blocks at {args.context_budget} tokens: total {sum(extra.values())}")
        return 0 if dry_run(cases, settings.llm_max_tokens, extra=extra) else 2
    if args.check_fingerprint:
        open_run = latest_open_run(args.split)
        if open_run is None:
            print("no open run")
            return 0
        recorded = json.loads((open_run / "run.json").read_text()).get("fingerprint")
        if recorded is None:
            print(f"{open_run.name}: no recorded fingerprint")
            return 2
        problems = fingerprint_mismatch(recorded, fingerprint(scored_cases(args.split, labels)))
        print(f"{open_run.name}: " + ("; ".join(problems) if problems else "fingerprint matches"))
        return 2 if problems else 0

    cache = None if args.no_cache else ResponseCache(CACHE_PATH, cache_only=args.cache_only)
    pinned = PinnedLLM(settings.eval_provider, settings.eval_model, cache)
    run_dir = latest_open_run(args.split) if args.resume else None
    if run_dir is None:
        sha, dirty = git_state()
        started = datetime.now(UTC)
        base_id = f"{args.split}-{started:%Y%m%dT%H%M%SZ}-{sha[:7]}"
        run_id, n = base_id, 1
        while (RESULTS / run_id).exists():  # two runs started in the same second
            n += 1
            run_id = f"{base_id}-{n}"
        run_dir = RESULTS / run_id
        run_dir.mkdir(parents=True)
        meta = {
            "run_id": run_id,
            "split": args.split,
            "git_sha": sha,
            "git_dirty": dirty,
            "provider": pinned.provider,
            "model": pinned.model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "eval_pr_title": EVAL_PR_TITLE,
            "started_at": started.isoformat(timespec="seconds"),
            "limit": args.limit,
            "cache_mode": "off" if args.no_cache else "only" if args.cache_only else "on",
            "scored_cases": len(cases),
            "order_seed": ORDER_SEED,
            "diff_transform": DIFF_TRANSFORM,
            "fingerprint": fingerprint(scored_cases(args.split, labels)),
            "case_order": [c["case_id"] for c in cases],
            "sessions": [],
        }
        (run_dir / "run.json").write_text(json.dumps(meta, indent=1) + "\n")
    meta = json.loads((run_dir / "run.json").read_text())
    if (meta["provider"], meta["model"]) != (pinned.provider, pinned.model):
        print(f"Refusing to resume {run_dir}: it pins {meta['provider']}/{meta['model']}.")
        return 2
    scored = scored_cases(args.split, labels)
    if "fingerprint" not in meta or "case_order" not in meta:
        print(f"Refusing to resume {run_dir}: it has no recorded fingerprint or case order.")
        return 2
    if problems := fingerprint_mismatch(meta["fingerprint"], fingerprint(scored)):
        print(f"Refusing to resume {run_dir}: " + "; ".join(problems) + ".")
        return 2
    by_id = {c["case_id"]: c for c in scored}
    cases = [by_id[cid] for cid in meta["case_order"]]  # the recorded order, never recomputed
    done = done_ids(run_dir)
    session = len(meta["sessions"]) + 1
    meta["sessions"].append(
        {"session": session, "started_at": now_iso(), "already_done": len(done)}
    )
    (run_dir / "run.json").write_text(json.dumps(meta, indent=1) + "\n")
    runner = Runner(
        pinned,
        cache,
        settings.llm_max_tokens,
        settings.llm_temperature,
        window=TokenWindow(limit=TOKENS_PER_MINUTE),
    )
    print(f"run {meta['run_id']}: {len(done)} of {len(cases)} cases already done")
    code = 0
    with (run_dir / "results.jsonl").open("a") as out:
        for case in cases:
            if case["case_id"] in done:
                continue
            try:
                case_started = now_iso()
                record = await runner.run_case(case)
                record = {
                    **record,
                    "session": session,
                    "started_at": case_started,
                    "finished_at": now_iso(),
                }
            except BudgetExhausted as exc:
                print(f"Stopped: rate-limit budget exhausted ({exc}). Resume with --resume.")
                code = 3
                break
            except CacheOnlyMiss as exc:
                print(f"FAILED: --cache-only run has no cached response for case {exc}.")
                code = 4
                break
            out.write(json.dumps(record) + "\n")
            out.flush()
            done.add(case["case_id"])
            print(f"{len(done)}/{len(cases)} {case['case_id']} {record['status']}", flush=True)
    meta["sessions"][-1].update(
        {
            "ended_at": now_iso(),
            "stop": {0: "complete", 3: "rate-limit budget", 4: "cache-only miss"}.get(code, code),
            "done_after": len(done),
            "provider_calls": runner.provider_calls,
        }
    )
    (run_dir / "run.json").write_text(json.dumps(meta, indent=1) + "\n")
    if cache is not None:
        rate = cache.hit_rate
        print(
            f"cache: {cache.hits} hits, {cache.misses} misses, hit rate "
            f"{'n/a' if rate is None else f'{rate:.1%}'}; provider calls {runner.provider_calls}"
        )
        cache.close()
    if code == 0 and len(done) == len(cases):
        from evals.metrics import write_summary  # noqa: PLC0415

        summary = write_summary(run_dir, cases, labels)
        print(f"summary: {run_dir / 'summary.json'}")
        print(json.dumps(summary["headline"], indent=1))
    return code


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(run(parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
