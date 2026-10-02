"""M3 Step 3: build benchmark cases from the mined candidates.

- Buggy case: the fix commit reversed, package source only (Q56), labeled with the lines the fix
  touched; discarded if the fix is cosmetic (whitespace, comments, docstrings, renames or
  annotations only).
- Clean case: a non-fix commit none of whose added or modified lines was changed by a bug-fix
  commit within the following 6 months (SZZ-style, Q60), sampled per size bucket to match the
  buggy distribution, at ~30% of all cases.
- 60/40 dev/holdout split stratified by repo and category; deterministic case IDs. Splits are
  frozen: a case already in dev.jsonl / holdout.jsonl never changes split.

    python -m evals.benchmark.build_cases
"""

import hashlib
import json
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
    clean_message,
    package_scoped,
    read_commits,
)
from evals.benchmark.szz import blamed_commits
from evals.benchmark.verify_repos import BUGFIX, REPOS_DIR, SELECTED, git

CLEAN_SHARE = 0.30
FOLLOW_UP = timedelta(days=183)  # "no bug fix in the following 6 months" (Q22)
DEV_SHARE = 0.60
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


def clean_pool(repo: str, package_dir: str) -> tuple[list[Commit], dict[str, int]]:
    """SZZ-style clean candidates (Q60) and the funnel counts behind them.

    A candidate passes the same filters as a buggy candidate (package source only, size limits)
    and is clean if no bug-fix commit within the following 6 months blames any line it added or
    modified. Behavioural-change filtering happens at sampling time.
    """
    history = [annotate(c) for c in read_commits(repo, package_dir, WINDOW_START, WINDOW_END)]
    fixes = [c for c in history if BUGFIX.search(c.message) and c.package_files]
    blamed_by: dict[str, list[date]] = defaultdict(list)
    funnel: Counter[str] = Counter()
    for fix in fixes:
        if not fix.parent:  # at the shallow-clone boundary: no parent to blame against
            funnel["fixes skipped: no parent in the clone"] += 1
            continue
        for sha in blamed_commits(repo_dir(repo), fix.sha, fix.parent, fix.package_files):
            blamed_by[sha].append(date.fromisoformat(fix.date))
    latest_start = WINDOW_END - FOLLOW_UP
    pool = []
    for c in history:
        day = date.fromisoformat(c.date)
        checks = (
            ("dated ≤ window end − 6 months", day <= latest_start),
            ("not a bug-fix message", not BUGFIX.search(c.message)),
            ("subject filter", not EXCLUDED_SUBJECT.search(c.subject)),
            ("package-scoped", package_scoped(c)),
            (
                "size ≤3 files / ≤60 lines",
                0 < c.package_lines <= MAX_LINES and len(c.package_files) <= MAX_FILES,
            ),
            (
                "no line blamed by a fix within 6 months",
                not any(day < d <= day + FOLLOW_UP for d in blamed_by.get(c.sha, [])),
            ),
        )
        funnel["commits in window"] += 1
        for name, ok in checks:
            if not ok:
                break
            funnel[name] += 1
        else:
            pool.append(c)
    return pool, dict(funnel)


def load_frozen() -> dict[str, dict[str, Any]]:
    """Cases already written to dev.jsonl / holdout.jsonl: their splits never change."""
    frozen = {}
    for split in ("dev", "holdout"):
        path = DATA / f"{split}.jsonl"
        if path.exists():
            for line in path.read_text().splitlines():
                case = json.loads(line)
                case["message"] = clean_message(case["message"])
                frozen[case["case_id"]] = case
    return frozen


def clean_case(repo: str, c: Commit) -> Case:
    diff = git(repo_dir(repo), "diff", "--no-color", c.parent, c.sha, "--", *c.package_files)
    return Case(
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


def build_clean(
    buggy: list[Case], frozen: dict[str, dict[str, Any]], discards: Counter[str]
) -> tuple[list[Case], dict[str, Any]]:
    """Keep frozen clean cases; top up each size bucket to match the buggy distribution."""
    target_total = round(len(buggy) * CLEAN_SHARE / (1 - CLEAN_SHARE))
    buggy_buckets = Counter(size_bucket(c.size_lines) for c in buggy)
    targets = {b: round(target_total * n / len(buggy)) for b, n in buggy_buckets.items()}

    chosen: dict[str, Case] = {}
    funnels: dict[str, dict[str, int]] = {}
    pools: dict[str, list[Commit]] = {}
    for repo, package_dir in SELECTED.items():
        pools[repo], funnels[repo] = clean_pool(repo, package_dir)
    pool_ids = {case_id(c.repo, c.sha) for commits in pools.values() for c in commits}
    for cid, case in frozen.items():
        if case["kind"] == "clean":
            chosen[cid] = Case(**case)
            if cid not in pool_ids:
                discards[
                    "frozen clean case no longer in the SZZ pool (kept: splits are frozen)"
                ] += 1

    shortfall: dict[str, Any] = {}
    for bucket, target in sorted(targets.items()):
        have = sum(1 for c in chosen.values() if size_bucket(c.size_lines) == bucket)
        # Spread new picks across repos in proportion to that repo's buggy cases in the bucket.
        weights = Counter(c.repo for c in buggy if size_bucket(c.size_lines) == bucket)
        candidates = {
            repo: [
                c
                for c in sorted(commits, key=lambda c: case_id(c.repo, c.sha))
                if size_bucket(c.package_lines) == bucket and case_id(repo, c.sha) not in chosen
            ]
            for repo, commits in pools.items()
        }
        picks_by_repo: Counter[str] = Counter()
        while have < target and any(candidates.values()):
            # Next repo: the one furthest below its weighted share, among repos with candidates.
            repo = min(
                (r for r in candidates if candidates[r]),
                key=lambda r: (picks_by_repo[r] / max(weights[r], 0.5), r),
            )
            c = candidates[repo].pop(0)
            if change_kind(repo, c.parent, c.sha, c.package_files) != "behavioural":
                discards["clean: cosmetic, typing-only or rename-only"] += 1
                continue
            chosen[case_id(repo, c.sha)] = clean_case(repo, c)
            picks_by_repo[repo] += 1
            have += 1
        if have < target:
            lo, hi = SIZE_BUCKETS[bucket]
            shortfall[f"{lo}-{hi}"] = {"target": target, "got": have}
    return list(chosen.values()), {"targets": targets, "shortfall": shortfall, "funnel": funnels}


def assign_splits(cases: list[Case], frozen: dict[str, str] | None = None) -> None:
    """60/40 within each repo × category stratum (clean and unlabeled are their own strata).

    Frozen cases keep their split. New cases fill each stratum towards 60/40 in case-ID order,
    so adding cases never moves an existing one.
    """
    frozen = frozen or {}
    strata: dict[tuple[str, str], list[Case]] = defaultdict(list)
    for c in cases:
        key = "clean" if c.kind == "clean" else (c.category_label or "unlabeled")
        strata[(c.repo, key)].append(c)
    for members in strata.values():
        members.sort(key=lambda c: c.case_id)
        target_dev = int(len(members) * DEV_SHARE + 0.5)
        dev = 0
        for c in members:
            if c.case_id in frozen:
                c.split = frozen[c.case_id]
                dev += c.split == "dev"
        for c in members:
            if c.case_id not in frozen:
                c.split = "dev" if dev < target_dev else "holdout"
                dev += c.split == "dev"


def quarter(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def main() -> None:
    discards: Counter[str] = Counter()
    frozen = load_frozen()
    buggy = build_buggy(load_candidates(), discards)
    frozen_buggy = {cid for cid, c in frozen.items() if c["kind"] == "buggy"}
    if frozen_buggy and frozen_buggy != {c.case_id for c in buggy}:
        raise SystemExit("the buggy case set changed; splits are frozen, so stop and investigate")
    clean, clean_info = build_clean(buggy, frozen, discards)
    cases = buggy + clean
    ids = [c.case_id for c in cases]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate case IDs")
    assign_splits(cases, {cid: c["split"] for cid, c in frozen.items()})
    moved = [
        c.case_id for c in cases if c.case_id in frozen and frozen[c.case_id]["split"] != c.split
    ]
    if moved:
        raise SystemExit(f"frozen cases changed split: {moved}")
    for split in ("dev", "holdout"):
        with (DATA / f"{split}.jsonl").open("w") as out:
            for c in sorted((c for c in cases if c.split == split), key=lambda c: c.case_id):
                out.write(json.dumps(asdict(c)) + "\n")

    def table(key: Any) -> dict[str, int]:
        return dict(sorted(Counter(key(c) for c in cases).items()))

    def median(values: list[int]) -> int:
        return sorted(values)[len(values) // 2] if values else 0

    report = {
        "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
        "total": len(cases),
        "by_kind": table(lambda c: c.kind),
        "by_split": table(lambda c: c.split),
        "by_kind_and_split": table(lambda c: f"{c.kind}/{c.split}"),
        "by_repo": table(lambda c: f"{c.repo}/{c.kind}/{c.split}"),
        "by_category": table(
            lambda c: (c.category_label or "null") if c.kind == "buggy" else "clean"
        ),
        "size_buckets": {
            kind: {
                f"{lo}-{hi}": sum(1 for c in cases if c.kind == kind and lo <= c.size_lines <= hi)
                for lo, hi in SIZE_BUCKETS
            }
            for kind in ("buggy", "clean")
        },
        "size_lines_median": {
            kind: median([c.size_lines for c in cases if c.kind == kind])
            for kind in ("buggy", "clean")
        },
        "ranges_per_buggy_case": dict(sorted(Counter(len(c.labels) for c in buggy).items())),
        "clean_targets_by_bucket": {
            f"{SIZE_BUCKETS[b][0]}-{SIZE_BUCKETS[b][1]}": t
            for b, t in sorted(clean_info["targets"].items())
        },
        "clean_shortfall": clean_info["shortfall"],
        "clean_pool_funnel": clean_info["funnel"],
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
    }
    (DATA / "build_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
