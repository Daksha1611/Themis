from typing import Any

import pytest

from evals.benchmark.label_report import render, summarize
from evals.benchmark.write_labels import record

SPANS = [
    {"file": "pkg/m.py", "line_start": 11, "line_end": 11},
    {"file": "pkg/m.py", "line_start": 30, "line_end": 30},
]


def case(
    cid: str,
    kind: str = "buggy",
    repo: str = "o/a",
    heuristic: str | None = "control-flow",
    spans: int = 2,
) -> dict[str, Any]:
    return {
        "case_id": cid,
        "kind": kind,
        "split": "dev",
        "repo": repo,
        "category_label": heuristic if kind == "buggy" else None,
        "labels": SPANS[:spans] if kind == "buggy" else [],
    }


def test_keep_record_carries_primary_and_contested_ranges() -> None:
    r = record(case("a"), {"id": "a", "v": "y", "cat": "control-flow", "pr": 1, "also": [2]}, "T")
    assert r["valid"] is True
    assert r["primary_range"] == {"index": 1, **SPANS[0]}
    assert r["primary_contested_with"] == [2]
    assert r["labeller"] == "assistant, evidence-grounded"


def test_drop_and_clean_records() -> None:
    drop = record(case("a"), {"id": "a", "v": "t", "note": "annotations only"}, "T")
    assert (drop["valid"], drop["drop_reason"]) == (False, "typing-only")
    clean = record(case("c", kind="clean"), {"id": "c", "clean": "s", "note": "why"}, "T")
    assert clean["clean_verdict"] == "suspicious"


@pytest.mark.parametrize(
    "decision",
    [
        {"v": "y", "cat": "not-a-category", "pr": 1},
        {"v": "y", "cat": "security-other", "pr": 1},  # needs a subcategory
        {"v": "y", "cat": "control-flow", "pr": 3},  # only two ranges
        {"v": "y", "cat": "control-flow", "pr": 1, "also": [1]},  # primary listed as contested
    ],
)
def test_invalid_decisions_are_rejected(decision: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        record(case("a"), {"id": "a", **decision}, "T")


def labelled() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    cases = [
        case("k1"),  # heuristic agrees, clear primary
        case("k2", heuristic=None, spans=1),  # heuristic null, single range
        case("k3", repo="o/b", heuristic="error-handling"),  # overridden, contested
        case("d1", repo="o/b"),
        case("d2"),
        case("c1", kind="clean"),
        case("c2", kind="clean", repo="o/b"),
    ]
    decisions = {
        "k1": {"v": "y", "cat": "control-flow", "pr": 2},
        "k2": {"v": "y", "cat": "control-flow", "pr": 1},
        "k3": {"v": "y", "cat": "type-or-contract", "pr": 1, "also": [2]},
        "d1": {"v": "o", "note": "external-compat: Python 3.99"},
        "d2": {"v": "n", "note": "design"},
        "c1": {"clean": "c"},
        "c2": {"clean": "s", "note": "looks off"},
    }
    labels = {c["case_id"]: record(c, decisions[c["case_id"]], "T") for c in cases}
    return cases, labels


def test_summary_counts_every_section() -> None:
    s = summarize(*labelled())
    assert (s["kept"], s["dropped"], s["clean"], s["unlabelled"]) == (3, 2, 2, [])
    assert s["per_repo"]["o/b"] == {"buggy": 2, "kept": 1, "dropped": 1, "clean": 1}
    assert s["drop_reasons"] == {"other": 1, "not-a-bug": 1}
    assert s["categories"] == {"control-flow": 2, "type-or-contract": 1}
    assert s["heuristic"] == {"agreed": 1, "null": 1, "overrode": 1}
    assert s["overrides"] == {("error-handling", "type-or-contract"): 1}
    assert s["coverage"] == {
        "single range": 1,
        "several ranges, clear primary": 1,
        "several ranges, contested": 1,
    }
    assert [cid for cid, _, _ in s["suspicious"]] == ["c2"]


def test_unlabelled_cases_are_reported() -> None:
    cases, labels = labelled()
    del labels["k1"]
    assert summarize(cases, labels)["unlabelled"] == ["k1"]


def test_report_has_all_eight_sections_and_noise_bounds() -> None:
    report = render(summarize(*labelled()), "dev", ["- provenance"])
    for n in range(1, 9):
        assert f"## {n}. " in report
    assert "Upper bound: 2/5 = 40.0%" in report  # every drop reason
    assert "Excluding `o`" in report and "1/5 = 20.0%" in report


def test_wilson_lower_bound() -> None:
    from evals.benchmark.label_report import wilson_lower

    assert round(wilson_lower(25, 25), 3) == 0.867
    assert wilson_lower(0, 0) == 0.0
    assert wilson_lower(5, 10) < 0.5
