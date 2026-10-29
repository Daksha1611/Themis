"""The one-command daily runner for eval plans (ADR-030): slot order, arm prompt-hash rule,
refusals, and the runner's frozen contexts."""

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from app.schemas import ReviewContext
from evals import runner, schedule
from tests.test_context import chunk_context
from tests.test_eval_harness import FINDING, bench, fake  # noqa: F401 (fixture)
from tests.test_llm import FakeLiteLLM

PLAN = {
    "name": "t",
    "split": "dev",
    "model": "groq/openai/gpt-oss-120b",
    "cache": "off",
    "arms": {
        "baseline": {"context_budget": 0, "estimated_days": 1.0},
        "context": {"context_budget": 100, "estimated_days": 2.0},
    },
    "order": [["context", 1], ["baseline", 1], ["context", 2]],
}


def plan_file(tmp_path: Path, plan: dict[str, Any] = PLAN) -> Path:
    path = tmp_path / "plan.yaml"
    path.write_text(json.dumps(plan))  # JSON is valid YAML
    return path


def fake_run(results: Path, split: str, label: dict[str, Any], done: bool, prompt: str) -> Path:
    run_dir = results / f"{split}-{label['arm']}{label['index']}"
    run_dir.mkdir(parents=True)
    meta = {"plan": label, "scored_cases": 3, "fingerprint": {"prompt_hash": prompt}}
    (run_dir / "run.json").write_text(json.dumps(meta))
    if done:
        (run_dir / "summary.json").write_text("{}")
    return run_dir


def test_plan_rejects_unknown_arms(tmp_path: Path) -> None:
    bad = {**PLAN, "order": [["nope", 1]]}
    with pytest.raises(ValueError, match="unknown arm"):
        schedule.load_plan(plan_file(tmp_path, bad))
    assert schedule.load_plan(plan_file(tmp_path))["cache"] == "off"


def test_next_slot_resumes_the_open_run_before_starting_another(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "RESULTS", tmp_path)
    assert schedule.next_slot(PLAN, schedule.assigned_runs(PLAN)) == ("context", 1, None)
    fake_run(tmp_path, "dev", {"name": "t", "arm": "context", "index": 1}, True, "h1")
    opened = fake_run(tmp_path, "dev", {"name": "t", "arm": "context", "index": 2}, False, "h1")
    assert schedule.next_slot(PLAN, schedule.assigned_runs(PLAN)) == ("context", 2, opened)


def test_an_arms_reference_is_its_first_run_or_the_configured_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "RESULTS", tmp_path)
    v2 = fake_run(tmp_path / "old", "dev", {"name": "other", "arm": "x", "index": 1}, True, "v2")
    baseline = {"context_budget": 0, "reference": str(v2)}
    plan = {**PLAN, "arms": {**PLAN["arms"], "baseline": baseline}}
    runs = schedule.assigned_runs(plan)
    assert schedule.reference_hash(plan, "baseline", runs) == "v2"
    assert schedule.reference_hash(plan, "context", runs) is None
    fake_run(tmp_path, "dev", {"name": "t", "arm": "context", "index": 1}, False, "c1")
    assert schedule.reference_hash(plan, "context", schedule.assigned_runs(plan)) == "c1"


async def test_run_next_refuses_a_different_model_or_a_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "RESULTS", tmp_path)
    assert await schedule.run_next({**PLAN, "model": "groq/other"}) == 2
    assert await schedule.run_next({**PLAN, "cache": "on"}) == 2


async def test_run_next_continues_until_the_quota_stops_a_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "RESULTS", tmp_path)
    calls: list[argparse.Namespace] = []

    async def fake_runner(args: argparse.Namespace) -> int:
        calls.append(args)
        done = len(calls) == 1  # the first run completes, the second hits the quota
        fake_run(tmp_path, "dev", args.plan, done, "h")
        return 0 if done else 3

    monkeypatch.setattr(runner, "run", fake_runner)
    assert await schedule.run_next(PLAN) == 3
    assert [(a.plan["arm"], a.plan["index"]) for a in calls] == [("context", 1), ("baseline", 1)]
    assert all(a.no_cache and a.split == "dev" for a in calls)
    assert [a.context_budget for a in calls] == [100, 0]
    assert calls[0].expect_prompt_hash is None  # no context run yet: run 1 sets the reference


def test_status_counts_quota_days_left(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "RESULTS", tmp_path)
    fake_run(tmp_path, "dev", {"name": "t", "arm": "context", "index": 1}, True, "h")
    lines = schedule.status_lines(PLAN)
    assert "  context run 1 (budget 100): complete dev-context1: 0/3 cases" in lines
    assert lines[-1] == "estimated quota days left: 3.0"


def test_inhibit_is_a_no_op_once_inside_systemd_inhibit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(schedule.INHIBITED, "1")
    schedule.inhibit(["next"])  # would exec otherwise


# --- runner: context runs and the expected prompt hash -------------------------------------


def contexts_for(cases: list[dict[str, Any]], budget: int) -> dict[str, ReviewContext]:
    return {c["case_id"]: chunk_context() for c in cases}


def test_a_context_run_freezes_its_contexts_and_sends_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake: Callable[..., FakeLiteLLM],  # noqa: F811
) -> None:
    results = bench(tmp_path, monkeypatch)
    monkeypatch.setattr(runner, "build_contexts", contexts_for)
    f = fake({"groq": FINDING})
    assert runner.main(["--split", "dev", "--no-cache", "--context-budget", "100"]) == 0
    run_dir = next(results.iterdir())
    assert len(runner.load_contexts(run_dir / "contexts.jsonl")) == 3
    assert json.loads((run_dir / "run.json").read_text())["context_budget"] == 100
    assert all("<context>" in c["messages"][0]["content"] for c in f.calls)
    record = json.loads((run_dir / "results.jsonl").read_text().splitlines()[0])
    assert record["context_chunks"] == 1


def test_a_run_with_unexpected_prompts_is_refused_before_it_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    results = bench(tmp_path, monkeypatch)
    args = runner.parse_args(["--split", "dev", "--no-cache"])
    args.expect_prompt_hash = "0" * 64
    import asyncio

    assert asyncio.run(runner.run(args)) == 2
    assert not results.exists() or not any(results.iterdir())
