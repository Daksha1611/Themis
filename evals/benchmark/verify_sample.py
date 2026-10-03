"""Owner verification sample for the dev labels (Q61 amendment).

    python -m evals.benchmark.verify_sample            # write verification_sample.md
    python -m evals.benchmark.verify_sample --score    # agreement rates from the owner's ticks

Selects SAMPLE_SIZE kept buggy dev cases, stratified across categories and repos:
- one case from each small category (fewer than MACRO_MIN kept cases);
- the remaining slots across the macro-eligible categories, at least MIN_PER_MACRO each, the rest
  by largest remainder in proportion to size;
- within a category, each pick goes to the repo furthest below its share of kept cases, ties
  broken by a seeded random choice.

The owner's borderline cases are added after the sample and scored separately: they were chosen
because they are hard, so counting them in the sample would bias the agreement rate.
"""

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

from evals.benchmark.label import DATA, LABELS, load_labels, numbered_diff
from evals.benchmark.label_report import MACRO_MIN, sha256

SEED = 20261003
SAMPLE_SIZE = 25
MIN_PER_MACRO = 3
BORDERLINE = ("2109faa46125df3d", "c06100e30fe371f9", "0f097b6d4ac12b55")  # owner, 2026-10-03
OUT = DATA / "verification_sample.md"
FIELDS = ("validity", "category", "primary range")
STRATIFIED = "## Stratified sample"
BORDER = "## Borderline cases"
CASE_HEADING = re.compile(r"^### \d+\. `([0-9a-f]{16})`", re.M)
TICK = re.compile(r"^- \[([ xX])\] (validity|category|primary range): (agree|disagree)\s*$", re.M)


def allocate(counts: dict[str, int], total: int, minimum: int) -> dict[str, int]:
    """Slots per category: at least `minimum` (or all its cases), the rest shared in proportion
    to category size by the largest-remainder method, never more than a category's cases."""
    quota = {c: min(minimum, n) for c, n in counts.items()}
    left = total - sum(quota.values())
    shares = {c: left * n / sum(counts.values()) for c, n in counts.items()}
    for c in counts:
        quota[c] += min(int(shares[c]), counts[c] - quota[c])
    order = sorted(counts, key=lambda c: (int(shares[c]) - shares[c], -counts[c], c))
    while sum(quota.values()) < total and any(quota[c] < counts[c] for c in counts):
        for c in order:
            if sum(quota.values()) < total and quota[c] < counts[c]:
                quota[c] += 1
    return quota


def select(
    cases: list[dict[str, Any]], labels: dict[str, dict[str, Any]], seed: int = SEED
) -> tuple[list[str], dict[str, int]]:
    """The stratified sample (case IDs in selection order) and the slots per category."""
    pool = sorted(
        (
            c
            for c in cases
            if c["kind"] == "buggy"
            and labels.get(c["case_id"], {}).get("valid") is True
            and c["case_id"] not in BORDERLINE
        ),
        key=lambda c: c["case_id"],
    )
    category = {c["case_id"]: labels[c["case_id"]]["category"] for c in pool}
    counts = Counter(category.values())
    small = sorted(c for c, n in counts.items() if n < MACRO_MIN)
    macro = {c: n for c, n in counts.items() if n >= MACRO_MIN}
    quota = {c: 1 for c in small} | allocate(macro, SAMPLE_SIZE - len(small), MIN_PER_MACRO)

    repo_share = Counter(c["repo"] for c in pool)
    target = {repo: SAMPLE_SIZE * n / len(pool) for repo, n in repo_share.items()}
    taken: Counter[str] = Counter()
    rng = random.Random(seed)  # noqa: S311 (reproducible sampling, not security)
    chosen: list[str] = []

    def need(c: dict[str, Any]) -> float:
        return taken[c["repo"]] / target[c["repo"]]

    # small categories first (forced), then the macro ones from the smallest
    for cat in [*small, *sorted(macro, key=lambda c: (macro[c], c))]:
        candidates = [c for c in pool if category[c["case_id"]] == cat]
        for _ in range(quota[cat]):
            lowest = min(need(c) for c in candidates)
            pick = rng.choice([c for c in candidates if need(c) == lowest])
            candidates.remove(pick)
            taken[pick["repo"]] += 1
            chosen.append(pick["case_id"])
    return chosen, quota


def assigned(record: dict[str, Any], case: dict[str, Any]) -> list[str]:
    if not record["valid"]:
        return [
            f"- **Validity:** dropped, `{record['drop_reason']}`",
            "- **Category / primary range:** none (dropped). If you would keep it, give the "
            "category and the primary range in the note.",
        ]
    primary = record["primary_range"]
    holding = sorted([primary["index"], *record.get("primary_contested_with", [])])
    return [
        "- **Validity:** kept (a genuine bug)",
        f"- **Category:** `{record['category']}`"
        + (f" ({record['subcategory']})" if record.get("subcategory") else ""),
        f"- **Primary range:** [{primary['index']}] `{primary['file']}` lines "
        f"{primary['line_start']}–{primary['line_end']} (of {len(case['labels'])} ranges)",
        "- **Ranges holding the bug** (strict recall, Q62): "
        + ", ".join(f"[{k}]" for k in holding),
    ]


def render_case(n: int, case: dict[str, Any], record: dict[str, Any]) -> str:
    evidence = record.get("evidence") or []
    message = case["message"].strip().splitlines()
    shown = message[:12] + (["…"] if len(message) > 12 else [])
    boxes = FIELDS if record["valid"] else FIELDS[:1]
    return "\n".join(
        [
            f"### {n}. `{case['case_id']}` · {case['repo']} · {case['date']}",
            "",
            f"- Commit: {case['url']}",
            "- Evidence read: "
            + (", ".join(evidence) if evidence else "none found upstream (commit only)"),
            "",
            "Commit message:",
            "",
            *(f"> {line}" if line else ">" for line in shown),
            "",
            "**Assigned labels**",
            "",
            *assigned(record, case),
            "",
            "<details><summary>Labeller's note (open after forming your own view)</summary>",
            "",
            record.get("note") or "(none)",
            "",
            "</details>",
            "",
            "Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):",
            "",
            "```",
            numbered_diff(case["diff"], case["labels"], color=False),
            "```",
            "",
            "**Your verdict** (tick one box per field)",
            "",
            *(f"- [ ] {field}: {answer}" for field in boxes for answer in ("agree", "disagree")),
            "- Note: ",
            "",
        ]
    )


def render(
    cases: dict[str, dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    chosen: list[str],
    quota: dict[str, int],
    labels_path: Path,
) -> str:
    repos = Counter(cases[cid]["repo"] for cid in chosen)
    out = [
        "# Label verification sample: dev split",
        "",
        "The dev labels were assigned by an LLM from human-written upstream evidence "
        "(Q61 amendment). This sample is for the project owner to verify by hand.",
        "",
        "**How to mark:** for each case, tick `agree` or `disagree` for each field; where you "
        "disagree, write the right value in the note. Validity asks whether the diff really "
        "reintroduces a bug (some real input would behave wrongly). Then run "
        "`python -m evals.benchmark.verify_sample --score`.",
        "",
        f"- Selection: `python -m evals.benchmark.verify_sample`, seed `{SEED}`",
        f"- Labels: `{labels_path}` (sha256 `{sha256(labels_path)}`)",
        f"- Stratified sample: {len(chosen)} kept buggy cases. Per category: "
        + ", ".join(f"{c} {k}" for c, k in sorted(quota.items(), key=lambda x: (-x[1], x[0]))),
        "- Per repo: " + ", ".join(f"{r} {k}" for r, k in sorted(repos.items())),
        f"- Borderline cases (owner's choice, scored separately): {len(BORDERLINE)}",
        "",
        f"{STRATIFIED} ({len(chosen)} cases)",
        "",
    ]
    out += [render_case(n, cases[cid], labels[cid]) for n, cid in enumerate(chosen, 1)]
    out += [f"{BORDER} ({len(BORDERLINE)} cases)", ""]
    out += [
        render_case(n, cases[cid], labels[cid]) for n, cid in enumerate(BORDERLINE, len(chosen) + 1)
    ]
    return "\n".join(out)


def parse(text: str) -> dict[str, dict[str, Any]]:
    """Per case: its section and, per field, 'agree', 'disagree', 'both', None (unticked), or
    'n/a' (no boxes: category and primary range of a dropped case)."""
    verdicts: dict[str, dict[str, Any]] = {}
    border_at = text.find(BORDER)
    headings = list(CASE_HEADING.finditer(text))
    for i, h in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        ticked: dict[str, set[str]] = {}
        present = set()
        for box, field, answer in TICK.findall(text[h.start() : end]):
            present.add(field)
            if box != " ":
                ticked.setdefault(field, set()).add(answer)
        verdicts[h.group(1)] = {
            "section": "borderline" if 0 <= border_at < h.start() else "sample",
            **{
                f: "n/a"
                if f not in present
                else ("both" if len(t) > 1 else next(iter(t)))
                if (t := ticked.get(f))
                else None
                for f in FIELDS
            },
        }
    return verdicts


def score(verdicts: dict[str, dict[str, Any]], section: str) -> dict[str, Counter[str]]:
    """Per field: counts of agree / disagree / both / unticked over one section."""
    return {
        f: Counter(v[f] or "unticked" for v in verdicts.values() if v["section"] == section)
        for f in FIELDS
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--score", action="store_true", help="score the owner's ticks")
    parser.add_argument("--force", action="store_true", help="overwrite a file with verdicts")
    args = parser.parse_args(argv)
    if args.score:
        verdicts = parse(OUT.read_text())
        for section in ("sample", "borderline"):
            print(f"{section}:")
            for field, counts in score(verdicts, section).items():
                decided = counts["agree"] + counts["disagree"]
                rate = f"{counts['agree'] / decided:.1%}" if decided else "n/a"
                extra = {k: n for k, n in counts.items() if k not in ("agree", "disagree")}
                print(f"  {field}: {counts['agree']}/{decided} agree ({rate}) {extra or ''}")
        return 0
    if OUT.exists() and re.search(r"^- \[[xX]\]", OUT.read_text(), re.M) and not args.force:
        print(f"{OUT} already has ticked verdicts; refusing to overwrite (use --force).")
        return 2
    lines = (DATA / "dev.jsonl").read_text().splitlines()
    cases = {c["case_id"]: c for c in map(json.loads, lines)}
    labels = load_labels(LABELS)
    chosen, quota = select(list(cases.values()), labels)
    OUT.write_text(render(cases, labels, chosen, quota, LABELS))
    print(f"wrote {OUT}: {len(chosen)} sampled + {len(BORDERLINE)} borderline cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
