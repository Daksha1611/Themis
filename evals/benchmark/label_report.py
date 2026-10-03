"""Label report for a labelled benchmark split: the eight sections the labelling pass reports.

    python -m evals.benchmark.label_report --split dev
    python -m evals.benchmark.label_report --split dev --write "docs/vault/08 Results/<note>.md"

Reads the split's cases and the latest label record per case from labels_human.jsonl. Prints the
report as Markdown; `--write` also saves it as a vault note with frontmatter. No LLM calls.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.benchmark.label import CATEGORIES, DATA, DROP_REASONS, LABELS, load_labels

MACRO_MIN = 5  # Metrics: macro recall only over categories with at least this many cases


def short_repo(repo: str) -> str:
    return repo.split("/")[-1]


def pct(part: int, whole: int) -> str:
    return f"{part / whole:.1%}" if whole else "n/a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def summarize(cases: list[dict[str, Any]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Every number the report prints, from the cases and their latest label records."""
    buggy = [c for c in cases if c["kind"] == "buggy"]
    clean = [c for c in cases if c["kind"] == "clean"]
    unlabelled = [c["case_id"] for c in cases if c["case_id"] not in labels]
    kept = [c for c in buggy if labels.get(c["case_id"], {}).get("valid") is True]
    dropped = [c for c in buggy if labels.get(c["case_id"], {}).get("valid") is False]

    repos = sorted({c["repo"] for c in cases})
    per_repo = {
        repo: {
            "buggy": sum(c["repo"] == repo for c in buggy),
            "kept": sum(c["repo"] == repo for c in kept),
            "dropped": sum(c["repo"] == repo for c in dropped),
            "clean": sum(c["repo"] == repo for c in clean),
        }
        for repo in repos
    }

    drop_reasons = Counter(labels[c["case_id"]]["drop_reason"] for c in dropped)
    other_notes = [
        (c["case_id"], short_repo(c["repo"]), labels[c["case_id"]]["note"])
        for c in dropped
        if labels[c["case_id"]]["drop_reason"] == DROP_REASONS["o"]
    ]

    categories = Counter(labels[c["case_id"]]["category"] for c in kept)

    heuristic: Counter[str] = Counter()
    overrides: Counter[tuple[str, str]] = Counter()
    for c in kept:
        guess, final = c.get("category_label"), labels[c["case_id"]]["category"]
        if guess is None:
            heuristic["null"] += 1
        elif guess == final:
            heuristic["agreed"] += 1
        else:
            heuristic["overrode"] += 1
            overrides[(guess, final)] += 1

    coverage: Counter[str] = Counter()
    for c in kept:
        if len(c["labels"]) == 1:
            coverage["single range"] += 1
        elif labels[c["case_id"]].get("primary_contested_with"):
            coverage["several ranges, contested"] += 1
        else:
            coverage["several ranges, clear primary"] += 1

    suspicious = [
        (c["case_id"], short_repo(c["repo"]), labels[c["case_id"]]["note"])
        for c in clean
        if labels.get(c["case_id"], {}).get("clean_verdict") == "suspicious"
    ]

    return {
        "total": len(cases),
        "buggy": len(buggy),
        "clean": len(clean),
        "unlabelled": unlabelled,
        "kept": len(kept),
        "dropped": len(dropped),
        "per_repo": per_repo,
        "drop_reasons": drop_reasons,
        "other_notes": other_notes,
        "categories": categories,
        "heuristic": heuristic,
        "overrides": overrides,
        "coverage": coverage,
        "suspicious": suspicious,
        "labellers": Counter(
            labels[c["case_id"]].get("labeller", "owner") for c in cases if c["case_id"] in labels
        ),
    }


def render(s: dict[str, Any], split: str, provenance: list[str]) -> str:
    kept, dropped, buggy = s["kept"], s["dropped"], s["buggy"]
    out = [
        f"# Label report: {split} split",
        "",
        *provenance,
        "",
        "## 1. Kept and dropped buggy cases",
        "",
        f"{buggy} buggy cases labelled: **{kept} kept ({pct(kept, buggy)})**, "
        f"**{dropped} dropped ({pct(dropped, buggy)})**. "
        f"{s['clean']} clean cases labelled ({s['total']} cases in all).",
        "",
        "| Repo | Buggy | Kept | Dropped | Kept % | Clean |",
        "|---|---|---|---|---|---|",
    ]
    for repo, r in s["per_repo"].items():
        out.append(
            f"| {repo} | {r['buggy']} | {r['kept']} | {r['dropped']} | "
            f"{pct(r['kept'], r['buggy'])} | {r['clean']} |"
        )
    out.append(f"| **All** | {buggy} | {kept} | {dropped} | {pct(kept, buggy)} | {s['clean']} |")

    out += ["", "## 2. Drop reasons", "", "| Reason | Count | Share of drops |", "|---|---|---|"]
    for key, reason in DROP_REASONS.items():
        n = s["drop_reasons"].get(reason, 0)
        out.append(f"| `{key}` {reason} | {n} | {pct(n, dropped)} |")
    external = sum(note.startswith("external-compat") for _, _, note in s["other_notes"])
    out += [
        "",
        f"`o` notes ({len(s['other_notes'])}; {external} are `external-compat`):",
        "",
    ]
    out += [f"- `{cid}` ({repo}): {note}" for cid, repo, note in s["other_notes"]]

    out += [
        "",
        "## 3. Categories of kept buggy cases",
        "",
        "| Category | Count | Share |",
        "|---|---|---|",
    ]
    present = sorted(s["categories"], key=lambda c: (-s["categories"][c], c))
    out += [f"| {c} | {s['categories'][c]} | {pct(s['categories'][c], kept)} |" for c in present]
    absent = [c for c in CATEGORIES if c not in s["categories"]]
    out += ["", "No kept cases: " + (", ".join(absent) or "none") + "."]

    h = s["heuristic"]
    out += [
        "",
        "## 4. Heuristic category vs final label (kept cases)",
        "",
        f"- Agreed: {h['agreed']}",
        f"- Overrode: {h['overrode']}",
        f"- Heuristic was null: {h['null']}",
        "",
        "Overrides (heuristic → label):",
        "",
    ]
    out += [
        f"- {guess} → {final}: {n}"
        for (guess, final), n in sorted(s["overrides"].items(), key=lambda x: (-x[1], x[0]))
    ]

    cov = s["coverage"]
    clear = cov["single range"] + cov["several ranges, clear primary"]
    out += [
        "",
        "## 5. Primary-range coverage (kept cases)",
        "",
        f"- Single labelled range: {cov['single range']}",
        f"- Several ranges, one clear primary: {cov['several ranges, clear primary']}",
        f"- Several ranges, contested (other ranges hold the same bug just as much: "
        f"its other half, or the same mistake on a parallel code path): "
        f"{cov['several ranges, contested']}",
        "",
        f"**Clear primary range: {clear}/{kept} ({pct(clear, kept)})**; contested: "
        f"{cov['several ranges, contested']}/{kept} "
        f"({pct(cov['several ranges, contested'], kept)}). "
        "Contested ranges are recorded per case in `primary_contested_with`.",
    ]

    out += [
        "",
        "## 6. Suspicious clean cases",
        "",
        f"{len(s['suspicious'])} of {s['clean']} clean cases marked suspicious "
        "(they stay clean cases):",
        "",
    ]
    out += [f"- `{cid}` ({repo}): {note}" for cid, repo, note in s["suspicious"]]

    not_o = dropped - s["drop_reasons"].get(DROP_REASONS["o"], 0)
    n_only = s["drop_reasons"].get(DROP_REASONS["n"], 0)
    out += [
        "",
        "## 7. Estimated label noise",
        "",
        f"- **Upper bound: {dropped}/{buggy} = {pct(dropped, buggy)}** of mined bug-fix cases "
        "were not usable bugs (every drop reason).",
        f"- Excluding `o` (some of which may be genuine bugs that could not be classified): "
        f"{not_o}/{buggy} = {pct(not_o, buggy)}.",
        f"- Dropped as `n` not-a-bug alone: {n_only}/{buggy} = {pct(n_only, buggy)}.",
    ]

    eligible = sorted((c for c in CATEGORIES if s["categories"].get(c, 0) >= MACRO_MIN), key=str)
    out += [
        "",
        f"## 8. Macro-recall eligible categories (≥{MACRO_MIN} kept cases)",
        "",
        ", ".join(f"{c} ({s['categories'][c]})" for c in eligible) or "none",
        "",
        "Below the threshold: "
        + (
            ", ".join(
                f"{c} ({s['categories'].get(c, 0)})"
                for c in CATEGORIES
                if 0 < s["categories"].get(c, 0) < MACRO_MIN
            )
            or "none"
        )
        + ".",
    ]
    return "\n".join(out) + "\n"


FRONTMATTER = """---
name: {name}
description: "Label report for the {split} split: kept/dropped, drop reasons, categories, \
heuristic agreement, primary-range coverage, suspicious clean cases, label noise."
type: reliability
status: done
tags: [reliability, benchmark]
related:
  - "[[Benchmark]]"
  - "[[Label Noise]]"
  - "[[Metrics]]"
---

"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=("dev", "holdout"), required=True)
    parser.add_argument("--labels", type=Path, default=LABELS)
    parser.add_argument("--write", type=Path, help="also save the report as this vault note")
    args = parser.parse_args(argv)
    cases_path = DATA / f"{args.split}.jsonl"
    cases = [json.loads(line) for line in cases_path.read_text().splitlines()]
    labels = load_labels(args.labels)
    summary = summarize(cases, labels)
    if summary["unlabelled"]:
        print(f"{len(summary['unlabelled'])} cases are not labelled yet; no report.")
        return 1
    labellers = ", ".join(f"{who} ({n})" for who, n in summary["labellers"].items())
    provenance = [
        f"- Split: `{args.split}` (`{cases_path}`, sha256 `{sha256(cases_path)}`)",
        f"- Labels: `{args.labels}` (sha256 `{sha256(args.labels)}`); "
        "the latest record per case counts",
        f"- Labelled by: {labellers}",
        f"- Generated: {datetime.now(UTC).date().isoformat()} by "
        f"`python -m evals.benchmark.label_report --split {args.split}`",
    ]
    report = render(summary, args.split, provenance)
    print(report)
    if args.write:
        args.write.write_text(FRONTMATTER.format(name=args.write.stem, split=args.split) + report)
        print(f"written to {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
