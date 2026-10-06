"""Determinism probe (owner request, 2026-10-06): how stable is the pinned model's output?

    python -m evals.probe [--cases 10] [--repeats 3]

Picks dev cases whose outcome flipped between baseline v1 and its identical no-cache rerun
(stratified across repos, buggy and clean), and calls each one `--repeats` times under:
  A: the current configuration (temperature 0, max_tokens 2048, model-default "medium" effort)
  C: A + reasoning_effort="low"
The seed setting was dropped (owner, 2026-10-06): every call lands on a different backend build
(system_fingerprint), so a best-effort seed cannot make the output reproducible.
`--resume DIR` continues a probe stopped at the daily limit, skipping calls already recorded.
The **response cache is bypassed** for the probe: every call goes to the provider. Calls go
straight to LiteLLM with the exact prompt the review path renders (v2: numbered diff, neutral
title, masking) and are parsed and line-validated the same way, but without the review path's
validation retry, so each call's raw output is what is compared. Settings are interleaved per
case, so a stop at the daily limit leaves balanced partial data. Results: evals/results/probe-*/.
"""

import argparse
import asyncio
import hashlib
import json
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.graph.baseline import drop_invalid_lines, normalize_paths, parse_findings
from evals.benchmark.label import LABELS, load_labels
from evals.metrics import case_outcomes, load_results
from evals.runner import (
    DAILY_LIMIT,
    TOKENS_PER_MINUTE,
    TokenWindow,
    estimate_tokens,
    rendered_prompt,
    scored_cases,
)

V1 = Path("evals/results/dev-20261004T085157Z-ad2fc7d")
RERUN = Path("evals/results/dev-20261004T130632Z-1033b35")
SEED = 20261006
SETTINGS: dict[str, dict[str, Any]] = {
    "A": {},
    "C": {"reasoning_effort": "low"},
}
FIELDS = ("detected", "strict_category", "flagged")


def flipped(cases: list[dict[str, Any]], labels: dict[str, dict[str, Any]]) -> list[str]:
    """Cases whose detection, strict category-correct or clean-flag outcome differed between
    v1 and its identical rerun."""
    outcomes = []
    for run in (V1, RERUN):
        records = {r["case_id"]: r for r in load_results(run)}
        outcomes.append(
            case_outcomes(cases, labels, {k: r["findings"] for k, r in records.items()})
        )
    first, second = outcomes
    return sorted(
        cid for cid in first if any(first[cid].get(f) != second[cid].get(f) for f in FIELDS)
    )


def select(
    cases: list[dict[str, Any]], ids: list[str], n: int, seed: int = SEED
) -> list[dict[str, Any]]:
    """Round-robin across repos, at least two clean cases, seeded."""
    by_id = {c["case_id"]: c for c in cases}
    rng = random.Random(seed)  # noqa: S311 (reproducible selection, not security)
    pool = [by_id[i] for i in ids]
    rng.shuffle(pool)
    clean = [c for c in pool if c["kind"] == "clean"][:2]
    chosen = list(clean)
    repos = sorted({c["repo"] for c in pool})
    while len(chosen) < n:
        added = False
        for repo in repos:
            options = [c for c in pool if c["repo"] == repo and c not in chosen]
            if options and len(chosen) < n:
                chosen.append(options[0])
                added = True
        if not added:
            break
    return chosen


async def call(messages: list[dict[str, str]], extra: dict[str, Any]) -> dict[str, Any]:
    import litellm  # noqa: PLC0415

    settings = get_settings()
    raw: Any = await litellm.acompletion(
        model=f"{settings.eval_provider}/{settings.eval_model}",
        messages=messages,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        api_key=settings.api_key_for(settings.eval_provider),
        **extra,
    )
    message = raw.choices[0].message
    reasoning = getattr(message, "reasoning", None) or getattr(message, "reasoning_content", None)
    return {
        "content": message.content or "",
        "reasoning_sha": hashlib.sha256((reasoning or "").encode()).hexdigest()[:16],
        "completion_tokens": raw.usage.completion_tokens,
        "prompt_tokens": raw.usage.prompt_tokens,
        "system_fingerprint": getattr(raw, "system_fingerprint", None),
    }


def recorded(out: Path) -> set[tuple[str, str, int]]:
    """(case, setting, repeat) calls already in the probe file, for --resume."""
    if not out.exists():
        return set()
    rows = [json.loads(line) for line in out.read_text().splitlines() if line]
    return {(r["case_id"], r["setting"], r["repeat"]) for r in rows}


async def probe(
    selected: list[dict[str, Any]], repeats: int, out: Path, done: set[tuple[str, str, int]]
) -> str:
    labels = load_labels(LABELS)
    window = TokenWindow(limit=TOKENS_PER_MINUTE)
    settings = get_settings()
    with out.open("a") as sink:
        for case in selected:
            messages = rendered_prompt(case)
            estimate = estimate_tokens(messages) + settings.llm_max_tokens
            for name, extra in SETTINGS.items():
                for repeat in range(repeats):
                    if (case["case_id"], name, repeat) in done:
                        continue
                    await window.reserve(estimate)
                    try:
                        result = await call(messages, extra)
                    except Exception as exc:
                        detail = str(exc)
                        status = getattr(exc, "status_code", None)
                        if status == 429 and DAILY_LIMIT.search(detail):
                            return f"stopped at the daily limit: {detail[:200]}"
                        if status == 429:
                            await asyncio.sleep(20)
                            result = await call(messages, extra)
                        else:
                            raise
                    findings, errors, _ = parse_findings(result["content"])
                    findings, _ = drop_invalid_lines(
                        normalize_paths(findings, case["diff"]), case["diff"]
                    )
                    found = [f.model_dump() for f in findings]
                    outcome = case_outcomes([case], labels, {case["case_id"]: found})[
                        case["case_id"]
                    ]
                    record = {
                        "case_id": case["case_id"],
                        "kind": case["kind"],
                        "repo": case["repo"],
                        "setting": name,
                        "params": extra,
                        "repeat": repeat,
                        "content_sha": hashlib.sha256(result["content"].encode()).hexdigest()[:16],
                        "parse_errors": len(errors),
                        "outcome": outcome,
                        "at": datetime.now(UTC).isoformat(timespec="seconds"),
                        **{
                            k: result[k]
                            for k in (
                                "reasoning_sha",
                                "completion_tokens",
                                "prompt_tokens",
                                "system_fingerprint",
                            )
                        },
                    }
                    sink.write(json.dumps(record) + "\n")
                    sink.flush()
                    print(
                        case["case_id"],
                        name,
                        repeat,
                        outcome,
                        record["completion_tokens"],
                        flush=True,
                    )
    return "complete"


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per setting: cases with byte-identical output across all repeats, cases with identical
    outcomes across all repeats, pairwise outcome disagreement per field, mean output tokens."""
    by: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        by[r["setting"]][r["case_id"]].append(r)
    out: dict[str, Any] = {}
    for setting, cases in sorted(by.items()):
        complete = {cid: rs for cid, rs in cases.items() if len(rs) >= 2}
        identical = sum(len({r["content_sha"] for r in rs}) == 1 for rs in complete.values())
        same_outcome = sum(
            all(len({json.dumps(r["outcome"].get(f)) for r in rs}) == 1 for f in FIELDS)
            for rs in complete.values()
        )
        pair_disagree: dict[str, list[float]] = defaultdict(list)
        for rs in complete.values():
            pairs = [(a, b) for i, a in enumerate(rs) for b in rs[i + 1 :]]
            for f in FIELDS:
                if f in rs[0]["outcome"]:
                    pair_disagree[f].append(
                        sum(a["outcome"][f] != b["outcome"][f] for a, b in pairs) / len(pairs)
                    )
        out[setting] = {
            "cases": len(complete),
            "calls": sum(len(rs) for rs in complete.values()),
            "byte_identical_cases": identical,
            "identical_outcome_cases": same_outcome,
            "pairwise_disagreement": {f: sum(v) / len(v) for f, v in pair_disagree.items() if v},
            "mean_completion_tokens": sum(
                r["completion_tokens"] for rs in complete.values() for r in rs
            )
            / max(1, sum(len(rs) for rs in complete.values())),
            "system_fingerprints": sorted(
                {str(r["system_fingerprint"]) for rs in complete.values() for r in rs}
            ),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--resume", type=Path, help="a probe directory to continue")
    args = parser.parse_args(argv)
    labels = load_labels(LABELS)
    cases = scored_cases("dev", labels)
    by_id = {c["case_id"]: c for c in cases}
    if args.resume is not None:
        out_dir = args.resume
        meta = json.loads((out_dir / "probe.json").read_text())
        selected = [by_id[i] for i in meta["selected"]]
        repeats = meta["repeats"]
    else:
        ids = flipped(cases, labels)
        selected = select(cases, ids, args.cases)
        repeats = args.repeats
        out_dir = Path(f"evals/results/probe-{datetime.now(UTC):%Y-%m-%dT%H%M}")
        out_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "flipped_v1_vs_rerun": ids,
            "selected": [c["case_id"] for c in selected],
            "settings": SETTINGS,
            "repeats": repeats,
            "cache": "bypassed: every call goes to the provider",
            "prompt": "rendered_prompt() at the current commit (v2 review path)",
        }
        (out_dir / "probe.json").write_text(json.dumps(meta, indent=1) + "\n")
    calls = out_dir / "calls.jsonl"
    stop = asyncio.run(probe(selected, repeats, calls, recorded(calls)))
    records = [json.loads(x) for x in (out_dir / "calls.jsonl").read_text().splitlines() if x]
    summary = {"stop": stop, **summarize(records)}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
