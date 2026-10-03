"""Eval harness: response cache, pinned LLM mode (ADR-024), runner, metrics. No network."""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from litellm import exceptions as litellm_exceptions

from app import llm
from app.graph.baseline import BaselineResult, run_baseline_review
from app.llm import LLMError, LLMResponse, PinnedLLM, complete
from evals import metrics, runner
from evals.cache import CacheMiss, ResponseCache
from tests.test_llm import MESSAGES, FakeLiteLLM

DIFF = """diff --git a/pkg/m.py b/pkg/m.py
--- a/pkg/m.py
+++ b/pkg/m.py
@@ -10,3 +10,3 @@ def f(xs):
     total = 0
-    for i in range(len(xs)):
+    for i in range(len(xs) + 1):
         total += xs[i]
@@ -30,2 +30,2 @@ def g(x):
-    return x
+    return x + 1
"""


def response(content: str = "[]", provider: str = "groq") -> LLMResponse:
    return LLMResponse(
        content=content,
        provider=provider,
        model="openai/gpt-oss-120b",
        prompt_tokens=100,
        completion_tokens=20,
        total_tokens=120,
        cost_usd=0.001,
        reasoning="thinking",
    )


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, Exception | str]], FakeLiteLLM]:
    def install(outcomes: dict[str, Exception | str]) -> FakeLiteLLM:
        f = FakeLiteLLM(outcomes)
        monkeypatch.setattr(llm.litellm, "acompletion", f)
        return f

    return install


# --- cache -------------------------------------------------------------------------------


def test_cache_round_trip_keeps_the_full_response(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "r.db")
    key = cache.key("groq", "m", MESSAGES, 0.0, 2048)
    assert cache.get(key) is None
    cache.put(key, response())
    assert cache.get(key) == response()  # reasoning, tokens, cost, provider, model
    assert (cache.hits, cache.misses) == (1, 1)
    cache.set_latency(key, 1234)
    assert cache.latency(key) == 1234 and cache.contains(key)
    assert (cache.hits, cache.misses) == (1, 1)  # contains() does not count


@pytest.mark.parametrize(
    "change",
    [
        {"provider": "gemini"},
        {"model": "other"},
        {"messages": [{"role": "user", "content": "changed"}]},
        {"temperature": 0.5},
        {"max_tokens": 1024},
    ],
)
def test_any_request_change_changes_the_key(change: dict[str, Any]) -> None:
    base: dict[str, Any] = {
        "provider": "groq",
        "model": "m",
        "messages": MESSAGES,
        "temperature": 0.0,
        "max_tokens": 2048,
    }
    assert ResponseCache.key(**base) != ResponseCache.key(**{**base, **change})


def test_cache_only_miss_raises(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "r.db", cache_only=True)
    with pytest.raises(CacheMiss):
        cache.get("missing")


# --- pinned mode (ADR-024) -----------------------------------------------------------------


async def test_pinned_mode_never_falls_through_the_cascade(
    fake: Callable[..., FakeLiteLLM],
) -> None:
    limited = litellm_exceptions.RateLimitError(
        message="Rate limit reached: tokens per minute", llm_provider="groq", model="m"
    )
    f = fake({"groq": limited, "gemini": "[]", "mistral": "[]", "openrouter": "[]"})
    with pytest.raises(LLMError) as raised:
        await complete(MESSAGES, pinned=PinnedLLM("groq", "openai/gpt-oss-120b"))
    assert f.providers_called == ["groq"]
    assert raised.value.status_code == 429 and "tokens per minute" in raised.value.detail


async def test_production_path_still_uses_the_cascade(fake: Callable[..., FakeLiteLLM]) -> None:
    limited = litellm_exceptions.RateLimitError(message="x", llm_provider="groq", model="m")
    f = fake({"groq": limited, "gemini": "[]", "mistral": "[]", "openrouter": "[]"})
    assert (await complete(MESSAGES)).provider == "gemini"
    assert f.providers_called == ["groq", "gemini"]


async def test_pinned_cache_hit_makes_no_call(
    fake: Callable[..., FakeLiteLLM], tmp_path: Path
) -> None:
    f = fake({"groq": "[]"})
    pinned = PinnedLLM("groq", "openai/gpt-oss-120b", ResponseCache(tmp_path / "r.db"))
    first = await complete(MESSAGES, pinned=pinned)
    second = await complete(MESSAGES, pinned=pinned)
    assert len(f.calls) == 1 and first == second


async def test_baseline_result_carries_the_error_for_the_runner(
    fake: Callable[..., FakeLiteLLM],
) -> None:
    fake({"groq": litellm_exceptions.RateLimitError("Limit tokens per day (TPD)", "groq", "m")})
    result = await run_baseline_review(DIFF, {}, PinnedLLM("groq", "openai/gpt-oss-120b"))
    assert result.status == "failed" and result.error_status == 429
    assert runner.classify(result) == "stop:rate-day"


# --- runner --------------------------------------------------------------------------------


def failed(status: int | None, detail: str, error_type: str = "LLMError") -> BaselineResult:
    return BaselineResult(
        status="failed",
        findings=[],
        llm_response=None,
        parse_errors=[detail],
        error_type=error_type,
        error_status=status,
        error_detail=detail,
    )


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (failed(429, "Rate limit reached ... tokens per minute (TPM)"), "retry:rate-minute"),
        (failed(429, "Rate limit reached ... tokens per day (TPD)"), "stop:rate-day"),
        (failed(413, "Request too large"), "failed:provider-limit"),
        (failed(400, "context_length_exceeded"), "failed:provider-limit"),
        (failed(503, "unavailable"), "retry:error"),
        (failed(401, "bad key"), "failed:provider-error"),
        (failed(None, "miss", "CacheMiss"), "stop:cache-miss"),
        (
            BaselineResult(status="failed", findings=[], llm_response=None, parse_errors=["x"]),
            "failed:parse",
        ),
    ],
)
def test_classify(result: BaselineResult, expected: str) -> None:
    assert runner.classify(result) == expected


def test_backoff_uses_the_providers_hint() -> None:
    assert runner.backoff_seconds("Please try again in 7.5s.", 1) == 8.0
    assert runner.backoff_seconds("try again in 1m2s", 1) == 62.5
    assert runner.backoff_seconds("", 3) == 16.0


async def test_token_window_waits_when_the_minute_is_full() -> None:
    now = [0.0]
    slept: list[float] = []

    async def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    window = runner.TokenWindow(limit=8000, clock=lambda: now[0], sleep=sleep)
    await window.reserve(5000)
    await window.reserve(5000)  # would exceed 8000 within the minute
    assert slept and now[0] >= 60


def run_case_with(results: list[BaselineResult]) -> tuple[runner.Runner, list[float]]:
    queue = list(results)
    slept: list[float] = []

    async def review(_diff: str, _meta: dict[str, Any], _llm: PinnedLLM) -> BaselineResult:
        return queue.pop(0)

    async def sleep(seconds: float) -> None:
        slept.append(seconds)

    window = runner.TokenWindow(limit=10**9)
    r = runner.Runner(PinnedLLM("groq", "m"), None, 2048, 0.0, window, review, sleep)
    return r, slept


CASE = {"case_id": "a" * 16, "kind": "buggy", "repo": "o/r", "diff": DIFF}


async def test_runner_backs_off_then_records_the_answer() -> None:
    ok = BaselineResult(status="success", findings=[], llm_response=response(), parse_errors=[])
    r, slept = run_case_with([failed(429, "tokens per minute"), ok])
    record = await r.run_case(CASE)
    assert record["status"] == "success" and record["provider_attempts"] == 2 and slept
    assert (record["provider"], record["pinned_provider"]) == ("groq", "groq")


async def test_runner_stops_on_daily_limit_and_on_persistent_minute_limits() -> None:
    r, _ = run_case_with([failed(429, "tokens per day (TPD)")])
    with pytest.raises(runner.BudgetExhausted):
        await r.run_case(CASE)
    r, _ = run_case_with([failed(429, "per minute")] * (runner.MAX_RATE_RETRIES + 1))
    with pytest.raises(runner.BudgetExhausted):
        await r.run_case(CASE)


async def test_oversized_request_is_recorded_not_rerouted() -> None:
    r, _ = run_case_with([failed(413, "Request too large for model")])
    record = await r.run_case(CASE)
    assert record["status"] == "failed:provider-limit" and record["provider_attempts"] == 1


def test_dry_run_reports_fit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "estimate_tokens", lambda _m: 1000)
    lines: list[str] = []
    assert runner.dry_run([CASE] * 3, 2048, lines.append) is True
    assert runner.dry_run([CASE] * 100, 2048, lines.append) is False  # 304,800 > 200,000
    assert any("responses average" in line for line in lines)
    monkeypatch.setattr(runner, "estimate_tokens", lambda _m: 7000)
    assert runner.dry_run([CASE], 2048, lines.append) is False  # 9,048 > 8,000 per request


def test_holdout_is_refused_without_the_flag(capsys: pytest.CaptureFixture[str]) -> None:
    assert runner.main(["--split", "holdout", "--dry-run"]) == 2
    assert "HOLDOUT SPLIT" in capsys.readouterr().err


# --- end to end: real review path, fake LiteLLM ---------------------------------------------

SPANS = [
    {"file": "pkg/m.py", "line_start": 11, "line_end": 11},
    {"file": "pkg/m.py", "line_start": 30, "line_end": 30},
]


def bench(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    base = {"repo": "o/r", "diff": DIFF, "labels": SPANS, "size_lines": 4, "split": "dev"}
    # distinct diffs: identical prompts would share one cached response
    cases = [
        {**base, "case_id": cid, "kind": kind, "diff": DIFF.replace("total = 0", f"total = {i}")}
        for i, (cid, kind) in enumerate(
            [("b1", "buggy"), ("b2", "buggy"), ("b3", "buggy"), ("c1", "clean")]
        )
    ]  # b3 is dropped below, so it is never sent
    cases[3]["labels"] = []
    (data / "dev.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cases))
    labels = [
        {
            "case_id": "b1",
            "valid": True,
            "category": "off-by-one-or-boundary",
            "primary_range": {"index": 1, **SPANS[0]},
            "primary_contested_with": [],
        },
        {
            "case_id": "b2",
            "valid": True,
            "category": "type-or-contract",
            "primary_range": {"index": 2, **SPANS[1]},
            "primary_contested_with": [],
        },
        {"case_id": "b3", "valid": False, "drop_reason": "feature"},
    ]
    (data / "labels.jsonl").write_text("".join(json.dumps(r) + "\n" for r in labels))
    monkeypatch.setattr(runner, "DATA", data)
    monkeypatch.setattr(runner, "LABELS", data / "labels.jsonl")
    monkeypatch.setattr(runner, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(runner, "CACHE_PATH", tmp_path / "responses.db")
    monkeypatch.setattr(runner, "TOKENS_PER_MINUTE", 10**9)
    return tmp_path / "results"


FINDING = json.dumps(
    [
        {
            "file": "pkg/m.py",
            "line_start": 11,
            "line_end": 11,
            "category": "off-by-one-or-boundary",
            "severity": "high",
            "message": "m",
            "suggestion": "s",
            "raw_llm_confidence": 0.9,
        }
    ]
)


def test_full_run_then_cache_only_rerun_is_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., FakeLiteLLM]
) -> None:
    results = bench(tmp_path, monkeypatch)
    f = fake({"groq": FINDING})
    assert runner.main(["--split", "dev"]) == 0
    assert len(f.calls) == 3  # b1, b2, c1; the dropped b3 is never sent
    first = json.loads(next(results.glob("*/summary.json")).read_text())
    assert first["provider"] == "groq" and first["operational"]["pinned_share"]["rate"] == 1.0

    f.calls.clear()
    assert runner.main(["--split", "dev", "--cache-only"]) == 0
    assert f.calls == []
    summaries = sorted(results.glob("*/summary.json"), key=lambda p: p.stat().st_mtime)
    second = json.loads(summaries[-1].read_text())
    assert second["reviewer"] == first["reviewer"]
    assert second["operational"]["cache"]["hit_rate"]["rate"] == 1.0


def test_resume_continues_after_the_daily_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., FakeLiteLLM]
) -> None:
    results = bench(tmp_path, monkeypatch)
    day = litellm_exceptions.RateLimitError("Limit 200000 tokens per day (TPD)", "groq", "m")
    fake({"groq": day})
    assert runner.main(["--split", "dev"]) == 3
    run_dir = next(results.iterdir())
    assert not (run_dir / "summary.json").exists()
    f = fake({"groq": FINDING})
    assert runner.main(["--split", "dev", "--resume"]) == 0
    assert len(f.calls) == 3 and (run_dir / "summary.json").exists()


def test_cache_only_run_fails_loudly_on_a_miss(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake: Callable[..., FakeLiteLLM]
) -> None:
    bench(tmp_path, monkeypatch)
    f = fake({"groq": FINDING})
    assert runner.main(["--split", "dev", "--cache-only"]) == 4
    assert f.calls == []


# --- metrics -------------------------------------------------------------------------------


def test_wilson_interval() -> None:
    low, high = metrics.wilson(25, 25)
    assert round(low, 3) == 0.867 and high == 1.0
    low, high = metrics.wilson(5, 10)
    assert round(low, 3) == 0.237 and round(high, 3) == 0.763
    assert metrics.wilson(0, 0) == (0.0, 1.0)


def test_location_match_uses_the_margin() -> None:
    span = {"file": "a.py", "line_start": 10, "line_end": 12}
    near = {"file": "a.py", "line_start": 15, "line_end": 15}
    assert metrics.hits(near, span) and not metrics.hits(near, span, margin=0)
    assert not metrics.hits({**near, "line_start": 16, "line_end": 16}, span)
    assert not metrics.hits({**near, "file": "b.py"}, span)


def test_first_changed_line_of_every_hunk() -> None:
    assert metrics.first_changed_lines(DIFF) == [("pkg/m.py", 11), ("pkg/m.py", 30)]
    deletion = "+++ b/x.py\n@@ -5,2 +5,1 @@\n a\n-b\n"
    assert metrics.first_changed_lines(deletion) == [("x.py", 5)]


def finding(line: int, category: str, file: str = "pkg/m.py") -> dict[str, Any]:
    return {"file": file, "line_start": line, "line_end": line, "category": category}


def test_tiers_modes_macro_floor_precision_and_false_positives() -> None:
    def case(cid: str, kind: str = "buggy", repo: str = "o/a", size: int = 3) -> dict[str, Any]:
        return {
            "case_id": cid,
            "kind": kind,
            "repo": repo,
            "size_lines": size,
            "labels": [*SPANS, {"file": "pkg/m.py", "line_start": 50, "line_end": 50}],
        }

    cases, labels, found = [], {}, {}
    # five control-flow cases (macro-eligible) and one CWE-20 case (below the floor)
    for i in range(5):
        cid = f"cf{i}"
        cases.append(case(cid))
        labels[cid] = {
            "valid": True,
            "category": "control-flow",
            "primary_range": {"index": 1},
            "primary_contested_with": [2],
        }
    cases.append(case("sec"))
    labels["sec"] = {"valid": True, "category": "CWE-20", "primary_range": {"index": 1}}
    found["cf0"] = [finding(11, "control-flow")]  # primary hit, right category
    found["cf1"] = [finding(30, "control-flow")]  # contested range: strict, not primary
    found["cf2"] = [finding(50, "control-flow")]  # auto-labelled only: lenient
    found["cf3"] = [finding(11, "error-handling")]  # location only
    cases += [case("c1", "clean", size=3), case("c2", "clean", "o/b", size=20)]
    found["c1"] = [finding(1, "control-flow")]

    m = metrics.evaluate(cases, labels, found)
    recall = m["recall"]
    assert recall["lenient"]["location"]["k"] == 4 and recall["lenient"]["category"]["k"] == 3
    assert recall["strict"]["location"]["k"] == 3 and recall["strict"]["category"]["k"] == 2
    assert recall["primary"]["location"]["k"] == 2 and recall["primary"]["category"]["k"] == 1
    assert recall["strict"]["category"]["n"] == 6
    assert m["macro"]["categories"] == {"control-flow": 5}  # CWE-20 below the floor
    assert m["macro"]["strict_category"] == pytest.approx(2 / 5)
    assert (
        m["precision"]["strict_location"]["k"] == 3 and m["precision"]["strict_location"]["n"] == 5
    )
    assert m["false_positives"]["overall"]["cases_with_finding"]["k"] == 1
    assert set(m["false_positives"]["by_size"]) == {"1-5", "16-30"}
    assert set(m["false_positives"]["by_repo"]) == {"o/a", "o/b"}
    assert m["false_positives"]["noise_floor"]["k"] == 3
    assert m["security"]["per_category"]["CWE-20"]["n"] == 1
    for value in (recall["strict"]["category"], m["precision"]["lenient_category"]):
        assert {"k", "n", "rate", "low", "high"} <= value.keys()


def test_chance_baseline_flags_first_changed_lines_with_the_top_category() -> None:
    labels = {
        "a": {"valid": True, "category": "type-or-contract"},
        "b": {"valid": True, "category": "type-or-contract"},
        "c": {"valid": True, "category": "control-flow"},
    }
    top = metrics.most_common_category(labels)
    assert top == "type-or-contract"
    assert metrics.chance_findings({"diff": DIFF}, top) == [finding(11, top), finding(30, top)]


def test_operational_reports_pinned_share_and_failures() -> None:
    base = {
        "pinned_provider": "groq",
        "pinned_model": "m",
        "parse_errors": [],
        "cached": False,
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "estimated_prompt_tokens": 9,
        "cost_usd_estimate": 0.001,
        "latency_ms": 100,
        "provider_attempts": 1,
    }
    records = [
        {**base, "status": "success", "provider": "groq", "model": "m"},
        {
            **base,
            "status": "failed:provider-limit",
            "provider": None,
            "model": None,
            "latency_ms": None,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        },
    ]
    op = metrics.operational(records)
    assert op["pinned_share"]["rate"] == 1.0 and op["failures"] == {"failed:provider-limit": 1}
    assert op["latency_ms"]["p95"] == 100.0


def test_asyncio_mode_is_auto() -> None:
    # the async tests above run under pytest-asyncio's auto mode
    assert asyncio.iscoroutinefunction(test_pinned_cache_hit_makes_no_call)
