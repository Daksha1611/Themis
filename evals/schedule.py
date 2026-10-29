"""Run an eval plan one quota day at a time (ADR-029, ADR-030).

    python -m evals.schedule next   [--plan evals/plans/m4.yaml] [--i-know-this-is-holdout]
    python -m evals.schedule status [--plan evals/plans/m4.yaml]

`next` resumes the plan's open run, or starts the next pending one, and keeps going until the
provider's daily quota stops it; then it prints what is done and what is left. It always runs
inside `systemd-inhibit --what=sleep:idle` (it re-executes itself under it), so the machine
cannot suspend mid-run. Every run is pinned to the plan's model, bypasses the response cache,
and is fingerprinted; within an arm every run must render the same prompts as the arm's
reference (prompt hash), so the arm's runs are k samples of one configuration.
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

from app.config import get_settings
from evals import runner

PLAN = Path("evals/plans/m4.yaml")
INHIBITED = "THEMIS_INHIBITED"


def load_plan(path: Path) -> dict[str, Any]:
    plan: dict[str, Any] = yaml.safe_load(path.read_text())
    for arm, index in plan["order"]:
        if arm not in plan["arms"]:
            raise ValueError(f"plan order names unknown arm {arm!r}")
        if not isinstance(index, int) or index < 1:
            raise ValueError(f"run index must be a positive integer, got {index!r}")
    return plan


def run_meta(run_dir: Path) -> dict[str, Any]:
    meta: dict[str, Any] = json.loads((run_dir / "run.json").read_text())
    return meta


def assigned_runs(plan: dict[str, Any]) -> dict[tuple[str, int], Path]:
    """(arm, index) -> run directory: explicit paths in the plan, else runs whose run.json
    carries this plan's label."""
    found: dict[tuple[str, int], Path] = {}
    for arm, spec in plan["arms"].items():
        for index, path in (spec.get("runs") or {}).items():
            found[(arm, int(index))] = Path(path)
    for run_json in sorted(runner.RESULTS.glob(f"{plan['split']}-*/run.json")):
        label = json.loads(run_json.read_text()).get("plan") or {}
        if label.get("name") == plan["name"]:
            found.setdefault((label["arm"], int(label["index"])), run_json.parent)
    return found


def done_count(run_dir: Path) -> int:
    return len(runner.done_ids(run_dir))


def state(run_dir: Path | None) -> str:
    if run_dir is None:
        return "pending"
    return "complete" if (run_dir / "summary.json").exists() else "open"


def reference_hash(plan: dict[str, Any], arm: str, runs: dict[tuple[str, int], Path]) -> str | None:
    """The prompt hash every run of `arm` must match: the configured reference run's, else the
    arm's lowest-numbered started run's (None before any run of the arm has started)."""
    spec = plan["arms"][arm]
    source = Path(spec["reference"]) if spec.get("reference") else None
    if source is None:
        started = sorted(i for a, i in runs if a == arm)
        source = runs[(arm, started[0])] if started else None
    if source is None:
        return None
    return str(run_meta(source)["fingerprint"]["prompt_hash"])


def status_lines(plan: dict[str, Any]) -> list[str]:
    runs = assigned_runs(plan)
    lines = [f"plan {plan['name']} ({plan['split']}, {plan['model']}, cache {plan['cache']})"]
    left_days = 0.0
    keys = sorted({*runs, *(tuple(k) for k in plan["order"])}, key=lambda k: (k[0], k[1]))
    for arm, index in keys:
        run_dir = runs.get((arm, index))
        st = state(run_dir)
        spec = plan["arms"][arm]
        detail = ""
        if run_dir is not None:
            meta = run_meta(run_dir)
            detail = f" {run_dir.name}: {done_count(run_dir)}/{meta['scored_cases']} cases"
        if st != "complete":
            fraction = 1.0
            if run_dir is not None:
                fraction = 1 - done_count(run_dir) / run_meta(run_dir)["scored_cases"]
            left_days += fraction * float(spec.get("estimated_days", 0))
        lines.append(f"  {arm} run {index} (budget {spec['context_budget']}): {st}{detail}")
    lines.append(f"estimated quota days left: {left_days:.1f}")
    return lines


def next_slot(
    plan: dict[str, Any], runs: dict[tuple[str, int], Path]
) -> tuple[str, int, Path | None] | None:
    """The open run if there is one, else the first pending run in plan order."""
    for arm, index in plan["order"]:
        if state(runs.get((arm, index))) == "open":
            return arm, index, runs[(arm, index)]
    for arm, index in plan["order"]:
        if (arm, index) not in runs:
            return arm, index, None
    return None


def runner_args(
    plan: dict[str, Any],
    arm: str,
    index: int,
    run_dir: Path | None,
    expected: str | None,
    holdout_ok: bool,
) -> argparse.Namespace:
    return argparse.Namespace(
        split=plan["split"],
        limit=None,
        resume=False,
        run_dir=run_dir,
        no_cache=True,
        cache_only=False,
        dry_run=False,
        context_budget=int(plan["arms"][arm]["context_budget"]),
        i_know_this_is_holdout=holdout_ok,
        check_fingerprint=False,
        plan={"name": plan["name"], "arm": arm, "index": index},
        expect_prompt_hash=expected,
    )


async def run_next(plan: dict[str, Any], holdout_ok: bool = False) -> int:
    """Run slots until the quota stops a run (3), a refusal (2) or the plan is done (0)."""
    settings = get_settings()
    pinned = f"{settings.eval_provider}/{settings.eval_model}"
    if pinned != plan["model"]:
        print(f"Refusing: the plan pins {plan['model']}, the eval settings pin {pinned}.")
        return 2
    if plan["cache"] != "off":
        print("Refusing: k-run plans must bypass the cache (cache: off).")
        return 2
    while True:
        runs = assigned_runs(plan)
        slot = next_slot(plan, runs)
        if slot is None:
            print("plan complete")
            return 0
        arm, index, run_dir = slot
        expected = reference_hash(plan, arm, runs)
        verb = "resuming" if run_dir else "starting"
        print(f"== {verb} {arm} run {index}" + (f" ({run_dir.name})" if run_dir else ""))
        code = await runner.run(runner_args(plan, arm, index, run_dir, expected, holdout_ok))
        if code != 0:
            return code


def inhibit(argv: list[str]) -> None:
    """Re-execute this command under systemd-inhibit, unless already under it."""
    if os.environ.get(INHIBITED) == "1":
        return
    tool = shutil.which("systemd-inhibit")
    if tool is None:
        print("Refusing: systemd-inhibit is not available, and the run must not be suspended.")
        raise SystemExit(2)
    os.environ[INHIBITED] = "1"
    os.execv(  # noqa: S606 (fixed program: systemd-inhibit wrapping this interpreter)
        tool,
        [
            tool,
            "--what=sleep:idle",
            "--who=themis",
            "--why=eval plan run",
            sys.executable,
            "-m",
            "evals.schedule",
            *argv,
        ],
    )


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("next", "status"))
    parser.add_argument("--plan", type=Path, default=PLAN)
    parser.add_argument("--i-know-this-is-holdout", action="store_true")
    args = parser.parse_args(argv)
    plan = load_plan(args.plan)
    if args.command == "status":
        print("\n".join(status_lines(plan)))
        return 0
    inhibit(argv)
    code = asyncio.run(run_next(plan, args.i_know_this_is_holdout))
    print({0: "done", 2: "refused", 3: "stopped at the daily quota", 4: "cache miss"}.get(code))
    print("\n".join(status_lines(plan)))
    if code == 3:
        print("Next: run `python -m evals.schedule next` again once the quota window frees up.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
