"""Precision filter (M5, ADR-030): dev-only rule, auto-labels, features, grouped folds,
threshold choice, and the ADR-029 statistics. No model download, no LLM calls."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from evals.metrics import aggregated_comparison, bootstrap_ci, permutation_test
from training import build_training_set as bts
from training import train_filter as tf

DIFF = """diff --git a/pkg/m.py b/pkg/m.py
--- a/pkg/m.py
+++ b/pkg/m.py
@@ -10,4 +10,4 @@ def f(x):
     a = 1
-    b = 2
+    b = 3
+    c = 4
     return a
"""


def test_holdout_case_ids_are_rejected() -> None:
    with pytest.raises(bts.HoldoutLeak, match="1 holdout case"):
        bts.require_dev_only({"dev1", "hold1"}, {"hold1", "hold2"})
    bts.require_dev_only({"dev1"}, {"hold1"})  # dev only: fine


def test_build_rejects_a_run_containing_a_holdout_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    holdout_case = next(iter(bts.holdout_ids()))
    run = tmp_path / "run"
    run.mkdir()
    (run / "results.jsonl").write_text(json.dumps({"case_id": holdout_case, "findings": []}))
    with pytest.raises(bts.HoldoutLeak):
        bts.build({"x": run})


def test_the_real_training_set_is_dev_only_and_matches_headline_precision() -> None:
    rows = tf.load_rows()  # raises on any holdout case
    by_run = {run: [r for r in rows if r["run"] == run] for run in bts.RUNS}
    # the label rule is the headline precision test: v1 74/108, rerun 74/117, v2 83/124
    assert [(sum(r["label"] for r in v), len(v)) for v in by_run.values()] == [
        (74, 108),
        (74, 117),
        (83, 124),
    ]
    assert all(r["label"] == 0 for r in rows if r["kind"] == "clean")


def test_diff_index_marks_changed_lines_and_hunk_size() -> None:
    index = bts.diff_index(DIFF)["pkg/m.py"]
    assert index[10] == (" ", 1, 3)  # context; 2 added + 1 removed in the hunk
    assert index[11] == ("+", 1, 3) and index[12] == ("+", 1, 3)
    assert 14 not in index


def finding(line: int, **extra: Any) -> dict[str, Any]:
    return {
        "file": "pkg/m.py",
        "line_start": line,
        "line_end": line,
        "category": "control-flow",
        "severity": "high",
        "message": "m",
        "suggestion": "s",
        "raw_llm_confidence": 0.8,
        **extra,
    }


def test_features_and_snippet_use_the_new_side_of_the_diff() -> None:
    case = {"size_lines": 3}
    f = bts.features(finding(11), case, bts.diff_index(DIFF))
    assert f["on_changed_line"] == 1.0 and f["hunk_changed_lines"] == 3
    assert bts.features(finding(10), case, bts.diff_index(DIFF))["on_changed_line"] == 0.0
    assert bts.snippet(DIFF, finding(11), around=0) == "+    b = 3"


def test_labels_follow_the_strict_range_rule() -> None:
    case = {
        "kind": "buggy",
        "labels": [{"file": "pkg/m.py", "line_start": 11, "line_end": 11}],
    }
    label = {"valid": True, "primary_range": {"index": 1}, "category": "control-flow"}
    assert bts.is_real(finding(13), case, label) == 1  # within ±3
    assert bts.is_real(finding(20), case, label) == 0
    assert bts.is_real(finding(11), {**case, "kind": "clean"}, None) == 0


def test_folds_group_cases_and_balance_kinds() -> None:
    cases = [{"case_id": f"b{i}", "kind": "buggy"} for i in range(10)] + [
        {"case_id": f"c{i}", "kind": "clean"} for i in range(5)
    ]
    folds = tf.assign_folds(cases)
    assert folds == tf.assign_folds(cases)  # seeded
    for k in range(tf.FOLDS):
        assert sum(folds[f"b{i}"] == k for i in range(10)) == 2
        assert sum(folds[f"c{i}"] == k for i in range(5)) == 1


def rows_for(labels: list[int], cases: list[str], run: str = "r") -> list[dict[str, Any]]:
    return [
        {"run": run, "case_id": c, "label": y, "kind": "buggy"}
        for y, c in zip(labels, cases, strict=True)
    ]


def test_threshold_maximises_precision_within_the_detection_floor() -> None:
    # case a: one real (0.9) and one noise (0.2) finding; case b: one noise (0.1) finding
    rows = rows_for([1, 0, 0], ["a", "a", "b"])
    scores = np.array([0.9, 0.2, 0.1])
    # dropping b's only finding loses half the detection: not allowed at a 5-point floor
    assert tf.choose_threshold(rows, scores, {"a", "b"}) <= 0.1  # keeps every finding
    # with a 50-point allowance the filter keeps only a's real finding
    assert tf.choose_threshold(rows, scores, {"a", "b"}, max_drop=0.5) == pytest.approx(0.9)


def test_permutation_and_bootstrap() -> None:
    assert permutation_test([0.0, 0.0]) == 1.0
    assert permutation_test([1.0] * 12) < 0.01
    assert permutation_test([1.0, -1.0] * 6) == 1.0
    low, high = bootstrap_ci([1.0] * 4 + [0.0] * 4)
    assert 1.0 <= low <= 4.0 <= high <= 7.0


def test_aggregated_comparison_reports_net_cases_over_run_means() -> None:
    first = [{"a": {"detected": True}, "b": {"detected": False}}] * 3
    second = [
        {"a": {"detected": True}, "b": {"detected": True}},
        {"a": {"detected": True}, "b": {"detected": True}},
        {"a": {"detected": True}, "b": {"detected": False}},
    ]
    result = aggregated_comparison(first, second)["detected"]
    assert result["cases"] == 2
    assert result["net_cases"] == pytest.approx(2 / 3)
