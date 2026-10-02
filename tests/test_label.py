import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from evals.benchmark import label

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


def case(
    cid: str, kind: str = "buggy", heuristic: str | None = "off-by-one-or-boundary"
) -> dict[str, Any]:
    return {
        "case_id": cid,
        "kind": kind,
        "split": "dev",
        "repo": "o/r",
        "url": "u",
        "date": "d",
        "message": "Fix loop",
        "diff": DIFF,
        "category_label": heuristic,
        "category_reason": "r",
        "labels": [
            {"file": "pkg/m.py", "line_start": 11, "line_end": 11},
            {"file": "pkg/m.py", "line_start": 30, "line_end": 30},
        ]
        if kind == "buggy"
        else [],
    }


def scripted(answers: list[str]) -> Iterator[str]:
    yield from answers


def run(cases: list[dict[str, Any]], path: Path, answers: list[str]) -> list[dict[str, Any]]:
    it = scripted(answers)
    label.run(
        cases, path, ask=lambda _q: next(it), say=lambda _m: None, color=False, now=lambda: "T"
    )
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_confirming_heuristic_category_is_one_keypress(tmp_path: Path) -> None:
    # valid=Enter, category=Enter (heuristic), primary range=2, note=Enter
    records = run([case("a")], tmp_path / "l.jsonl", ["", "", "2", ""])
    assert records[0]["valid"] is True
    assert records[0]["category"] == "off-by-one-or-boundary"
    assert records[0]["heuristic_category"] == "off-by-one-or-boundary"
    assert records[0]["primary_range"] == {
        "index": 2,
        "file": "pkg/m.py",
        "line_start": 30,
        "line_end": 30,
    }


def test_drop_with_reason(tmp_path: Path) -> None:
    records = run([case("a")], tmp_path / "l.jsonl", ["f", "adds a parameter"])
    assert records[0] == {
        "case_id": "a",
        "kind": "buggy",
        "split": "dev",
        "heuristic_category": "off-by-one-or-boundary",
        "valid": False,
        "drop_reason": "feature",
        "note": "adds a parameter",
        "labelled_at": "T",
    }


def test_category_by_number_and_invalid_input_is_reasked(tmp_path: Path) -> None:
    number = str(label.CATEGORIES.index("arithmetic-or-numeric") + 1)
    records = run(
        [case("a", heuristic=None)], tmp_path / "l.jsonl", ["y", "", "99", number, "", ""]
    )  # Enter with no default and 99 are rejected
    assert records[0]["category"] == "arithmetic-or-numeric"
    assert records[0]["primary_range"]["index"] == 1


def test_resume_skips_labelled_cases(tmp_path: Path) -> None:
    path = tmp_path / "l.jsonl"
    run([case("a"), case("b")], path, ["f", "", "q"])  # label a, quit on b
    records = run([case("a"), case("b")], path, ["n", ""])  # resumes at b
    assert [r["case_id"] for r in records] == ["a", "b"]
    assert records[1]["drop_reason"] == "not-a-bug"


def test_back_relabels_previous_case(tmp_path: Path) -> None:
    path = tmp_path / "l.jsonl"
    records = run([case("a"), case("b")], path, ["f", "", "b", "n", "", "t", ""])
    assert [(r["case_id"], r["drop_reason"]) for r in records] == [
        ("a", "feature"),
        ("a", "not-a-bug"),
        ("b", "typing-only"),
    ]
    assert label.load_labels(path)["a"]["drop_reason"] == "not-a-bug"  # last record wins


def test_clean_case_verdicts(tmp_path: Path) -> None:
    records = run(
        [case("a", kind="clean"), case("b", kind="clean")],
        tmp_path / "l.jsonl",
        ["", "s", "touches a hot path"],
    )
    assert records[0]["clean_verdict"] == "looks clean"
    assert records[1] == {
        "case_id": "b",
        "kind": "clean",
        "split": "dev",
        "heuristic_category": "off-by-one-or-boundary",
        "clean_verdict": "suspicious",
        "note": "touches a hot path",
        "labelled_at": "T",
    }


def test_holdout_is_refused_without_freeze(tmp_path: Path) -> None:
    said: list[str] = []
    code = label.main(
        ["--split", "holdout", "--labels", str(tmp_path / "l.jsonl")],
        ask=lambda _q: "q",
        say=said.append,
    )
    assert code == 2
    assert any("Refusing" in s for s in said)


def test_numbered_diff_marks_labelled_ranges() -> None:
    shown = label.numbered_diff(DIFF, case("a")["labels"], color=False).splitlines()
    assert any(line.startswith("[1]") and "range(len(xs) + 1)" in line for line in shown)
    assert any(line.startswith("[2]") and "return x + 1" in line for line in shown)


def test_help_text_carries_the_precedence_rules() -> None:
    help_text = label.category_help()
    assert "Index and length arithmetic" in help_text
