from app.taxonomy import LOGIC_CATEGORIES, SECURITY_CATEGORIES
from evals.benchmark.build_cases import Case, assign_splits, case_id, size_bucket
from evals.benchmark.labeling import (
    CWE_RULES,
    LOGIC_RULES,
    Span,
    classify_change,
    infer_category,
    label_spans,
)
from evals.benchmark.mine_commits import is_package_source, is_support_file

REVERSED = """diff --git a/pkg/m.py b/pkg/m.py
--- a/pkg/m.py
+++ b/pkg/m.py
@@ -10,4 +10,4 @@ def f(xs):
     total = 0
-    for i in range(len(xs)):
+    for i in range(len(xs) + 1):
         total += xs[i]
     return total
@@ -30,3 +30,2 @@ def g(x):
     y = x
-    if y is None:
-        return 0
     return y
"""


def test_rules_cover_the_taxonomy_exactly() -> None:
    assert {c for c, _, _ in LOGIC_RULES} == set(LOGIC_CATEGORIES)
    assert {c for c, _ in CWE_RULES} == set(SECURITY_CATEGORIES)


def test_label_spans_use_new_side_lines() -> None:
    spans = label_spans(REVERSED)
    assert spans[0] == Span("pkg/m.py", 11, 11)  # the replaced line
    assert spans[1] == Span("pkg/m.py", 30, 31)  # a pure deletion: lines around the gap


def test_cosmetic_changes_are_detected() -> None:
    code = "def f(x):\n    return x + 1\n"
    assert classify_change(code, "def f(x):  # comment\n\n    return x + 1\n") == "cosmetic"
    assert classify_change(code, 'def f(x):\n    """Doc."""\n    return x + 1\n') == "cosmetic"
    assert classify_change(code, "def f(x: int) -> int:\n    return x + 1\n") == "annotation"
    assert classify_change(code, "def f(value):\n    return value + 1\n") == "rename"
    assert classify_change(code, "def f(x):\n    return x - 1\n") == "behavioural"


def test_inconsistent_renaming_is_behavioural() -> None:
    before = "def f(a, b):\n    return a - b\n"
    after = "def f(a, b):\n    return b - a\n"  # swapped operands: a real change
    assert classify_change(before, after) == "behavioural"
    assert classify_change(None, after) == "behavioural"  # file added


def test_category_precedence_matches_adr_023() -> None:
    handled = "+    except ZeroDivisionError:\n+        return 0\n"
    assert infer_category("Fix crash", "Fix crash", handled).label == "error-handling"
    computed = "+    return total / count\n"
    msg = "Fix division by zero in average"
    assert infer_category(msg, msg, computed).label == "arithmetic-or-numeric"


def test_category_signals() -> None:
    msg = "Fix race when cancelling a task group"
    assert infer_category(msg, msg, "+    await x\n").label == "concurrency-or-async"
    msg = "Fix SQL injection in query builder (security)"
    assert infer_category(msg, msg, "").label == "CWE-89"
    msg = "Fix the thing"
    assert infer_category(msg, msg, "").label is None  # unclear stays unlabeled


def test_case_ids_are_stable() -> None:
    assert case_id("a/b", "deadbeef") == case_id("a/b", "deadbeef")
    assert case_id("a/b", "deadbeef") != case_id("a/c", "deadbeef")
    assert len(case_id("a/b", "deadbeef")) == 16


def _case(i: int, category: str | None) -> Case:
    return Case(
        case_id=f"{i:016x}",
        kind="buggy",
        repo="r/x",
        commit=str(i),
        parent="p",
        date="2025-08-01",
        subject="",
        message="",
        url="",
        linked_issue=None,
        pr_ref=None,
        diff="",
        files=[],
        size_lines=3,
        size_files=1,
        labels=[],
        category_label=category,
        category_reason="",
    )


def test_splits_are_60_40_per_stratum_and_deterministic() -> None:
    cases = [_case(i, "control-flow") for i in range(10)] + [_case(i, None) for i in range(10, 15)]
    assign_splits(cases)
    first = [c.split for c in cases]
    assign_splits(list(reversed(cases)))
    assert [c.split for c in cases] == first
    flow = [c.split for c in cases if c.category_label == "control-flow"]
    assert flow.count("dev") == 6 and flow.count("holdout") == 4
    unlabeled = [c.split for c in cases if c.category_label is None]
    assert unlabeled.count("dev") == 3


def test_file_classification_and_size_buckets() -> None:
    assert is_package_source("src/click/core.py", "src/click/")
    assert not is_package_source("tests/test_core.py", "src/click/")
    assert is_support_file("CHANGES.md") and is_support_file("tests/test_x.py")
    assert [size_bucket(n) for n in (1, 5, 6, 30, 60)] == [0, 0, 1, 2, 3]


def test_szz_line_helpers() -> None:
    from evals.benchmark.szz import added_lines, removed_ranges

    diff = (
        "diff --git a/p.py b/p.py\n--- a/p.py\n+++ b/p.py\n"
        "@@ -3,2 +3,2 @@\n-a\n-b\n+A\n+B\n@@ -10,0 +11,1 @@\n+new\n"
    )
    assert removed_ranges(diff) == {"p.py": [(3, 4)]}  # pure addition at line 11: nothing to blame
    assert added_lines(diff) == {"p.py": {3, 4, 11}}


def test_frozen_cases_never_move() -> None:
    cases = [_case(i, "control-flow") for i in range(10)]
    frozen = {f"{i:016x}": "holdout" for i in range(5)}  # pretend the first five were frozen
    assign_splits(cases, frozen)
    assert all(c.split == "holdout" for c in cases[:5])
    assert sum(c.split == "dev" for c in cases) == 5  # new cases fill dev towards the target


def test_commit_trailers_are_stripped() -> None:
    from evals.benchmark.mine_commits import clean_message

    message = "Fix x\n\nBody.\n\nCo-authored-by: Someone <a@b>\nAssisted-by: Tool:model\n"
    assert clean_message(message) == "Fix x\n\nBody."
