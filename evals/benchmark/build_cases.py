"""M3 Step 3: build benchmark cases from the mined candidates.

- Buggy case: the fix commit reversed, package source only (Q56), labeled with the lines the fix
  touched; discarded if the fix is cosmetic (whitespace, comments, docstrings, renames or
  annotations only).
- Clean case: a non-fix commit whose package files saw no bug fix in the following 6 months,
  sampled to match the buggy size distribution, at ~30% of all cases.
- 60/40 dev/holdout split stratified by repo and category; deterministic case IDs.

    python -m evals.benchmark.build_cases
"""

import hashlib
import json
import random
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from evals.benchmark.labeling import classify_change, infer_category, label_spans
from evals.benchmark.mine_commits import (
    DATA,
    EXCLUDED_SUBJECT,
    MAX_FILES,
    MAX_LINES,
    WINDOW_END,
    WINDOW_START,
    Commit,
    FileChange,
    annotate,
    package_scoped,
    read_commits,
)
from evals.benchmark.verify_repos import BUGFIX, REPOS_DIR, SELECTED, git

CLEAN_SHARE = 0.30
FOLLOW_UP = timedelta(days=183)  # "no bug fix in the following 6 months" (Q22)
DEV_SHARE = 0.60
SAMPLE_SIZE = 15
SAMPLE_SEED = 20261002
SIZE_BUCKETS = ((1, 5), (6, 15), (16, 30), (31, 60))


@dataclass
class Case:
    case_id: str
    kind: str  # "buggy" | "clean"
    repo: str
    commit: str
    parent: str
    date: str
    subject: str
    message: str
    url: str
    linked_issue: str | None
    pr_ref: str | None
    diff: str
    files: list[str]
    size_lines: int
    size_files: int
    labels: list[dict[str, Any]]
    category_label: str | None
    category_reason: str
    split: str = ""


def case_id(repo: str, sha: str) -> str:
    """Stable and deterministic: the precision filter's holdout guard (M5) depends on it."""
    return hashlib.sha256(f"{repo}:{sha}".encode()).hexdigest()[:16]


def repo_dir(repo: str) -> Path:
    return REPOS_DIR / repo.replace("/", "__")


def show(repo: str, rev: str, path: str) -> str | None:
    try:
        return git(repo_dir(repo), "show", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return None  # file absent at that revision


def size_bucket(lines: int) -> int:
    return next(i for i, (lo, hi) in enumerate(SIZE_BUCKETS) if lo <= lines <= hi)


def change_kind(repo: str, before: str, after: str, files: list[str]) -> str:
    kinds = {classify_change(show(repo, before, f), show(repo, after, f)) for f in files}
    if "behavioural" in kinds:
        return "behavioural"
    return sorted(kinds)[0]


def load_candidates() -> list[Commit]:
    commits = []
    for line in (DATA / "candidates.jsonl").read_text().splitlines():
        raw = json.loads(line)
        raw["files"] = [FileChange(**f) for f in raw["files"]]
        commits.append(Commit(**raw))
    return commits


def build_buggy(candidates: list[Commit], discards: Counter[str]) -> list[Case]:
    cases = []
    for c in candidates:
        kind = change_kind(c.repo, c.parent, c.sha, c.package_files)
        if kind != "behavioural":
            discards[kind] += 1
            continue
        # The fix reversed, package source only: base = fixed code, head = buggy code.
        diff = git(repo_dir(c.repo), "diff", "--no-color", c.sha, c.parent, "--", *c.package_files)
        spans = label_spans(diff)
        if not diff.strip() or not spans:
            discards["empty after restricting to package source"] += 1
            continue
        category = infer_category(c.subject, c.message, diff)
        cases.append(
            Case(
                case_id=case_id(c.repo, c.sha),
                kind="buggy",
                repo=c.repo,
                commit=c.sha,
                parent=c.parent,
                date=c.date,
                subject=c.subject,
                message=c.message,
                url=f"https://github.com/{c.repo}/commit/{c.sha}",
                linked_issue=c.linked_issue,
                pr_ref=c.pr_ref,
                diff=diff,
                files=c.package_files,
                size_lines=c.package_lines,
                size_files=len(c.package_files),
                labels=[asdict(s) for s in spans],
                category_label=category.label,
                category_reason=category.reason,
            )
        )
    return cases


def clean_pool(repo: str, package_dir: str) -> list[Commit]:
    """Non-fix commits whose package files saw no bug fix in the following 6 months."""
    # History through the window end, so every candidate has a full 6-month follow-up.
    history = [annotate(c) for c in read_commits(repo, package_dir, WINDOW_START, WINDOW_END)]
    fixes = [c for c in history if BUGFIX.search(c.message) and c.package_files]
    latest_start = WINDOW_END - FOLLOW_UP
    pool = []
    for c in history:
        day = date.fromisoformat(c.date)
        if (
            day > latest_start
            or BUGFIX.search(c.message)
            or EXCLUDED_SUBJECT.search(c.subject)
            or not package_scoped(c)
            or not (0 < c.package_lines <= MAX_LINES and len(c.package_files) <= MAX_FILES)
        ):
            continue
        touched = set(c.package_files)
        fixed_later = any(
            touched & set(f.package_files) and day < date.fromisoformat(f.date) <= day + FOLLOW_UP
            for f in fixes
        )
        if not fixed_later:
            pool.append(c)
    return pool


def build_clean(buggy: list[Case], discards: Counter[str]) -> tuple[list[Case], dict[str, Any]]:
    """Sample clean cases per repo, matching that repo's buggy size distribution."""
    target_total = round(len(buggy) * CLEAN_SHARE / (1 - CLEAN_SHARE))
    per_repo = Counter(c.repo for c in buggy)
    shortfall: dict[str, Any] = {}
    cases: list[Case] = []
    for repo, package_dir in SELECTED.items():
        want = round(target_total * per_repo[repo] / len(buggy))
        buckets = Counter(size_bucket(c.size_lines) for c in buggy if c.repo == repo)
        pool = clean_pool(repo, package_dir)
        by_bucket: dict[int, list[Commit]] = defaultdict(list)
        for c in sorted(pool, key=lambda c: case_id(c.repo, c.sha)):
            by_bucket[size_bucket(c.package_lines)].append(c)
        chosen: list[Commit] = []
        for bucket, n_buggy in sorted(buckets.items()):
            quota = round(want * n_buggy / per_repo[repo])
            for c in by_bucket[bucket]:
                if len(chosen) >= want or quota == 0:
                    break
                if change_kind(repo, c.parent, c.sha, c.package_files) != "behavioural":
                    discards["clean: cosmetic"] += 1
                    continue
                chosen.append(c)
                quota -= 1
        if len(chosen) < want:
            shortfall[repo] = {"wanted": want, "got": len(chosen), "pool": len(pool)}
        for c in chosen:
            diff = git(
                repo_dir(repo), "diff", "--no-color", c.parent, c.sha, "--", *c.package_files
            )
            cases.append(
                Case(
                    case_id=case_id(repo, c.sha),
                    kind="clean",
                    repo=repo,
                    commit=c.sha,
                    parent=c.parent,
                    date=c.date,
                    subject=c.subject,
                    message=c.message,
                    url=f"https://github.com/{repo}/commit/{c.sha}",
                    linked_issue=c.linked_issue,
                    pr_ref=c.pr_ref,
                    diff=diff,
                    files=c.package_files,
                    size_lines=c.package_lines,
                    size_files=len(c.package_files),
                    labels=[],
                    category_label=None,
                    category_reason="clean case",
                )
            )
    return cases, shortfall


def assign_splits(cases: list[Case]) -> None:
    """60/40 within each repo × category stratum (clean and unlabeled are their own strata)."""
    strata: dict[tuple[str, str], list[Case]] = defaultdict(list)
    for c in cases:
        key = "clean" if c.kind == "clean" else (c.category_label or "unlabeled")
        strata[(c.repo, key)].append(c)
    for members in strata.values():
        members.sort(key=lambda c: c.case_id)
        n_dev = int(len(members) * DEV_SHARE + 0.5)
        for i, c in enumerate(members):
            c.split = "dev" if i < n_dev else "holdout"


def quarter(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def write_sample(cases: list[Case]) -> Path:
    """15 random dev cases for the owner's hand-check (never holdout)."""
    dev = sorted((c for c in cases if c.split == "dev"), key=lambda c: c.case_id)
    # Seeded and reproducible on purpose; not a security use.
    sample = random.Random(SAMPLE_SEED).sample(dev, min(SAMPLE_SIZE, len(dev)))  # noqa: S311
    path = DATA / "sample_for_review.md"
    lines = [
        "# Benchmark sample for hand review",
        "",
        f"{len(sample)} cases drawn at random (seed {SAMPLE_SEED}) from the **dev** split only.",
        "For each case, check: is the fix a genuine bug fix (buggy) or a change with no bug",
        "(clean)? Do the labeled lines cover the bug? Is the category right (or rightly null)?",
        "",
    ]
    for i, c in enumerate(sample, 1):
        lines += [
            f"## {i}. `{c.case_id}` · {c.kind} · {c.repo}",
            "",
            f"- Commit: {c.url} ({c.date})",
            f"- Linked issue: {c.linked_issue or '—'} · PR: {c.pr_ref or '—'}",
            f"- Category label: **{c.category_label or 'null'}** ({c.category_reason})",
            "- Labeled spans: "
            + (
                ", ".join(f"`{s['file']}` {s['line_start']}–{s['line_end']}" for s in c.labels)
                or "none (clean case)"
            ),
            f"- Size: {c.size_lines} lines in {c.size_files} file(s)",
            "",
            "Original commit message:",
            "",
            "```text",
            c.message,
            "```",
            "",
            "Diff shown to the reviewer"
            + (" (the fix reversed, package source only):" if c.kind == "buggy" else ":"),
            "",
            "```diff",
            c.diff.rstrip("\n"),
            "```",
            "",
            "Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · "
            "category right? ☐ yes ☐ no",
            "",
        ]
    path.write_text("\n".join(lines))
    return path


def main() -> None:
    discards: Counter[str] = Counter()
    buggy = build_buggy(load_candidates(), discards)
    clean, shortfall = build_clean(buggy, discards)
    cases = buggy + clean
    ids = [c.case_id for c in cases]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate case IDs")
    assign_splits(cases)
    for split in ("dev", "holdout"):
        with (DATA / f"{split}.jsonl").open("w") as out:
            for c in sorted((c for c in cases if c.split == split), key=lambda c: c.case_id):
                out.write(json.dumps(asdict(c)) + "\n")
    sample_path = write_sample(cases)

    def table(key: Any) -> dict[str, int]:
        return dict(sorted(Counter(key(c) for c in cases).items()))

    report = {
        "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
        "total": len(cases),
        "by_kind": table(lambda c: c.kind),
        "by_split": table(lambda c: c.split),
        "by_kind_and_split": table(lambda c: f"{c.kind}/{c.split}"),
        "by_repo": table(lambda c: f"{c.repo}/{c.kind}"),
        "by_category": table(
            lambda c: c.category_label or "null" if c.kind == "buggy" else "clean"
        ),
        "category_by_split": table(
            lambda c: (
                f"{c.category_label or 'null'}/{c.split}"
                if c.kind == "buggy"
                else f"clean/{c.split}"
            )
        ),
        "size_buckets": {
            kind: {
                f"{lo}-{hi}": sum(1 for c in cases if c.kind == kind and lo <= c.size_lines <= hi)
                for lo, hi in SIZE_BUCKETS
            }
            for kind in ("buggy", "clean")
        },
        "size_lines_median": {
            kind: sorted(c.size_lines for c in cases if c.kind == kind)[
                len([c for c in cases if c.kind == kind]) // 2
            ]
            for kind in ("buggy", "clean")
            if any(c.kind == kind for c in cases)
        },
        "buggy_dates_by_quarter": {
            repo: dict(sorted(Counter(quarter(c.date) for c in buggy if c.repo == repo).items()))
            for repo in SELECTED
        },
        "buggy_after_mid_2025": {
            repo: f"{sum(c.date >= '2025-07-01' for c in buggy if c.repo == repo)}/"
            f"{sum(c.repo == repo for c in buggy)}"
            for repo in SELECTED
        },
        "discards": dict(discards),
        "null_category_buggy": sum(c.category_label is None for c in buggy),
        "clean_shortfall": shortfall,
        "sample": str(sample_path),
    }
    (DATA / "build_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
