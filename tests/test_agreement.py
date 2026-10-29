"""Cross-run agreement and voting (ADR-031 Step 1): matching, clusters, support, the merged
review, and the build gate. No LLM calls."""

from typing import Any

from evals import agreement as ag


def f(line: int, category: str = "control-flow", file: str = "m.py") -> dict[str, Any]:
    return {"file": file, "line_start": line, "line_end": line, "category": category}


def test_matching_needs_file_and_lines_within_three_and_category_when_strict() -> None:
    assert ag.matches(f(10), f(13), strict=True)
    assert not ag.matches(f(10), f(14), strict=True)
    assert not ag.matches(f(10), f(10, file="n.py"), strict=False)
    assert not ag.matches(f(10), f(10, "error-handling"), strict=True)
    assert ag.matches(f(10), f(10, "error-handling"), strict=False)


def test_clusters_join_runs_and_count_distinct_runs() -> None:
    runs = [[f(10), f(40)], [f(12)], [f(11), f(80)]]
    found = sorted(ag.clusters(runs, strict=True), key=lambda c: -len(c))
    assert [ag.support(c) for c in found] == [3, 1, 1]
    # two findings of the same run are not matched to each other directly
    same_run = ag.clusters([[f(10), f(11)]], strict=True)
    assert sorted(ag.support(c) for c in same_run) == [1, 1]


def test_voting_keeps_clusters_with_enough_support() -> None:
    cases = [{"case_id": "a"}, {"case_id": "b"}]
    runs = [{"a": [f(10)], "b": [f(5)]}, {"a": [f(11)]}, {"a": [f(30)]}]
    two = ag.voted(cases, runs, m=2, strict=True)
    assert [x["line_start"] for x in two["a"]] == [10] and two["b"] == []
    assert len(ag.voted(cases, runs, m=1, strict=True)["a"]) == 2


def test_location_mode_takes_the_majority_category() -> None:
    cluster = [(0, f(10, "x")), (1, f(10, "y")), (2, f(11, "y"))]
    assert ag.representative(cluster, strict=False)["category"] == "y"
    assert ag.representative(cluster[:2], strict=False)["category"] == "x"  # tie: first run


def stats(kind: str, flagged: float) -> dict[str, Any]:
    return {"kind": kind, "flagged": flagged, "category": 0.0, "findings": flagged, "real": 0.0}


def test_gate_needs_a_material_clean_cut_within_the_detection_limit() -> None:
    ref = [stats("buggy", 1.0)] * 20 + [stats("clean", 1.0)] * 20
    cut = [stats("buggy", 1.0)] * 20 + [stats("clean", 0.0)] * 20
    rows = {"single run (mean of k)": ref, "rule": cut, "chance baseline": ref}
    result = {
        "paired": ag.paired(rows),
        "rules": {n: {"point": ag.headline(v)} for n, v in rows.items()},
    }
    assert ag.gate(result) == ["rule"]
    blunt = [stats("buggy", 0.0)] * 20 + [stats("clean", 0.0)] * 20  # detection lost
    rows["rule"] = blunt
    result = {
        "paired": ag.paired(rows),
        "rules": {n: {"point": ag.headline(v)} for n, v in rows.items()},
    }
    assert ag.gate(result) == []
