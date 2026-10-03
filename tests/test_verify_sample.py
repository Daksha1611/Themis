from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from evals.benchmark import verify_sample as vs
from evals.benchmark.fetch_evidence import linked_issues
from evals.benchmark.write_labels import record

DIFF = """diff --git a/pkg/m.py b/pkg/m.py
--- a/pkg/m.py
+++ b/pkg/m.py
@@ -10,2 +10,2 @@ def f(xs):
-    for i in range(len(xs)):
+    for i in range(len(xs) + 1):
"""
SPAN = {"file": "pkg/m.py", "line_start": 10, "line_end": 10}
# kept cases per category: four macro-eligible (>=5) and two small ones
SIZES = {
    "type-or-contract": 20,
    "control-flow": 10,
    "concurrency-or-async": 6,
    "error-handling": 5,
    "resource-leak": 2,
    "CWE-20": 1,
}
REPOS = ("o/a", "o/b", "o/c")


def case(cid: str, repo: str) -> dict[str, Any]:
    return {
        "case_id": cid,
        "kind": "buggy",
        "split": "dev",
        "repo": repo,
        "url": "u",
        "date": "d",
        "message": "Fix it",
        "diff": DIFF,
        "category_label": None,
        "labels": [SPAN],
    }


def dataset() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    cases, labels = [], {}
    n = 0
    for cat, size in SIZES.items():
        for _ in range(size):
            c = case(f"{n:016x}", REPOS[n % len(REPOS)])
            labels[c["case_id"]] = record(c, {"id": "", "v": "y", "cat": cat, "pr": 1}, "T")
            cases.append(c)
            n += 1
    for cid in vs.BORDERLINE:  # kept, so it must be kept out of the stratified pool
        c = case(cid, "o/a")
        labels[cid] = record(c, {"id": "", "v": "y", "cat": "type-or-contract", "pr": 1}, "T")
        cases.append(c)
    return cases, labels


def test_allocation_floors_each_category_then_shares_by_size() -> None:
    quota = vs.allocate({"a": 34, "b": 17, "c": 9, "d": 6}, 19, 3)
    assert quota == {"a": 6, "b": 5, "c": 4, "d": 4}
    assert vs.allocate({"a": 2, "b": 30}, 10, 3) == {"a": 2, "b": 8}  # never above a size


def test_selection_is_stratified_and_deterministic() -> None:
    cases, labels = dataset()
    chosen, quota = vs.select(cases, labels)
    assert chosen == vs.select(cases, labels)[0]  # same seed, same sample
    assert len(chosen) == vs.SAMPLE_SIZE == len(set(chosen))
    assert not set(chosen) & set(vs.BORDERLINE)
    picked = Counter(labels[cid]["category"] for cid in chosen)
    assert picked["resource-leak"] == picked["CWE-20"] == 1  # one per small category
    assert all(picked[c] >= vs.MIN_PER_MACRO for c in SIZES if SIZES[c] >= 5)
    assert dict(picked) == quota
    repos = Counter(c["repo"] for c in cases if c["case_id"] in chosen)
    assert max(repos.values()) - min(repos.values()) <= 2  # spread across repos


def test_render_has_unticked_boxes_and_dropped_cases_ask_validity_only(tmp_path: Path) -> None:
    cases, labels = dataset()
    dropped = vs.BORDERLINE[1]
    labels[dropped] = record(cases[-2], {"id": "", "v": "n", "note": "policy"}, "T")
    chosen, quota = vs.select(cases, labels)
    path = tmp_path / "labels.jsonl"
    path.write_text("{}\n")
    text = vs.render({c["case_id"]: c for c in cases}, labels, chosen, quota, path)
    assert "- [x]" not in text
    verdicts = vs.parse(text)
    assert len(verdicts) == vs.SAMPLE_SIZE + len(vs.BORDERLINE)
    assert sum(v["section"] == "borderline" for v in verdicts.values()) == len(vs.BORDERLINE)
    block = text[text.index(f"`{dropped}`") :]
    block = block[: block.index("- Note:")]
    assert "validity: agree" in block and "category: agree" not in block
    assert verdicts[dropped]["category"] == verdicts[dropped]["primary range"] == "n/a"


@pytest.mark.parametrize(
    ("ticks", "expected"),
    [
        (["validity: agree"], "agree"),
        (["validity: disagree"], "disagree"),
        (["validity: agree", "validity: disagree"], "both"),
        ([], None),
    ],
)
def test_parse_reads_ticked_boxes(ticks: list[str], expected: str | None) -> None:
    boxes = [
        f"- [{'x' if f'{field}: {answer}' in ticks else ' '}] {field}: {answer}"
        for field in vs.FIELDS
        for answer in ("agree", "disagree")
    ]
    text = "\n".join([vs.STRATIFIED, "### 1. `00000000000000aa` · o/a · d", *boxes, ""])
    verdict = vs.parse(text)["00000000000000aa"]
    assert verdict["validity"] == expected and verdict["category"] is None
    assert vs.score({"x": verdict}, "sample")["validity"][expected or "unticked"] == 1


def test_issue_links_skip_code_blocks_comments_and_template_examples() -> None:
    body = (
        "Fixes #12. See https://github.com/o/r/issues/34\n"
        "<!-- e.g. Fixes #56 -->\n```\n- entry (#78)\n```\n"
    )
    assert linked_issues("o/r", [body], exclude={12}) == [34]
    template = "If, say, your patch fixes issue #123, the entry should look like this: #9"
    assert linked_issues("agronholm/anyio", [template], exclude=set()) == [9]


def test_refuses_to_overwrite_a_file_with_verdicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "verification_sample.md"
    out.write_text("- [x] validity: agree\n")
    monkeypatch.setattr(vs, "OUT", out)
    assert vs.main([]) == 2
    assert out.read_text() == "- [x] validity: agree\n"
