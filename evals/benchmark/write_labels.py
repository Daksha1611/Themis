"""Append label decisions to labels_human.jsonl in the labelling tool's record schema.

Used for the evidence-grounded labelling pass (Q61 amendment): each decision is made after
reading the case's upstream PR and issue threads (`fetch_evidence.py`), and each record names its
labeller and the evidence URLs read.

    python -m evals.benchmark.write_labels decisions.json

A decision: {"id": case_id, "v": "y"|"f"|"t"|"r"|"n"|"o", "cat": category, "sub": subcategory,
"pr": primary range number, "also": [range numbers], "note": str} for buggy cases;
{"id", "clean": "c"|"s", "note"} for clean cases. "also" lists other ranges that hold the same bug
just as much as the primary one (the other half of it, or the same mistake on a parallel code
path); an empty list means the primary range is clear.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.taxonomy import SECURITY_OTHER
from evals.benchmark.fetch_evidence import CACHE
from evals.benchmark.label import CATEGORIES, DROP_REASONS, LABELS

LABELLER = "assistant, evidence-grounded"


def evidence_urls(case_id: str) -> list[str]:
    path = CACHE / f"{case_id}.json"
    if not path.exists():
        return []
    ev = json.loads(path.read_text())
    return [x["url"] for x in ev.get("pull_requests", []) + ev.get("issues", []) if x.get("url")]


def record(case: dict[str, Any], d: dict[str, Any], now: str) -> dict[str, Any]:
    base = {
        "case_id": case["case_id"],
        "kind": case["kind"],
        "split": case["split"],
        "heuristic_category": case.get("category_label"),
        "labeller": LABELLER,
        "evidence": evidence_urls(case["case_id"]),
    }
    if case["kind"] == "clean":
        verdict = {"c": "looks clean", "s": "suspicious"}[d["clean"]]
        return {**base, "clean_verdict": verdict, "note": d.get("note", ""), "labelled_at": now}
    if d["v"] != "y":
        return {
            **base,
            "valid": False,
            "drop_reason": DROP_REASONS[d["v"]],
            "note": d.get("note", ""),
            "labelled_at": now,
        }
    if d["cat"] not in CATEGORIES:
        raise ValueError(f"{case['case_id']}: unknown category {d['cat']!r}")
    if d["cat"] == SECURITY_OTHER and not d.get("sub"):
        raise ValueError(f"{case['case_id']}: security-other needs a subcategory")
    spans = case["labels"]
    index = d.get("pr", 1)
    if not 1 <= index <= len(spans):
        raise ValueError(f"{case['case_id']}: primary range {index} out of 1..{len(spans)}")
    contested = sorted(set(d.get("also", [])))
    if index in contested or not all(1 <= k <= len(spans) for k in contested):
        raise ValueError(f"{case['case_id']}: contested ranges {contested} invalid")
    return {
        **base,
        "valid": True,
        "category": d["cat"],
        "subcategory": d.get("sub"),
        "primary_range": {"index": index, **spans[index - 1]},
        "primary_contested_with": contested,
        "note": d.get("note", ""),
        "labelled_at": now,
    }


def main(path: str) -> None:
    cases = {
        json.loads(line)["case_id"]: json.loads(line)
        for line in Path("evals/benchmark/data/dev.jsonl").read_text().splitlines()
    }
    decisions = json.loads(Path(path).read_text())
    now = datetime.now(UTC).isoformat(timespec="seconds")
    records = [record(cases[d["id"]], d, now) for d in decisions]  # validate all before writing
    with LABELS.open("a") as out:
        for r in records:
            out.write(json.dumps(r) + "\n")
    print(f"appended {len(records)} records to {LABELS}")


if __name__ == "__main__":
    main(sys.argv[1])
