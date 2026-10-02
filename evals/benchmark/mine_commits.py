"""M3 Step 2: mine candidate bug-fix commits from the selected repos.

Walks non-merge commits on each repo's default branch in a fixed window and keeps commits that
look like small, package-local bug fixes. Size limits count package source only (Q56).

    python -m evals.benchmark.mine_commits

Writes evals/benchmark/data/candidates.jsonl and evals/benchmark/data/mining_report.json.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from evals.benchmark.verify_repos import (
    BUGFIX,
    CI_PATH,
    DOC_PATH,
    ISSUE_LINK,
    PR_REF,
    SELECTED,
    TEST_PATH,
    clone,
    git,
)

WINDOW_START = date(2025, 4, 1)
WINDOW_END = date(2026, 10, 1)  # fixed, so mining is reproducible
MAX_FILES = 3  # package source files
MAX_LINES = 60  # changed package source lines (added + removed)
EXCLUDED_SUBJECT = re.compile(
    r"\b(refactor\w*|typos?|docs?|documentation|docstrings?|format(ting|ted)?|lint(ing)?|style"
    r"|bump(s|ed)?|versions?|release[sd]?|deps|dependenc(y|ies)|changelog|readme|revert\w*|ci)\b",
    re.IGNORECASE,
)
DATA = Path("evals/benchmark/data")
FILTERS = (
    "non-merge commits in window",
    "bug-fix message",
    "package-scoped",
    "size ≤3 package files and ≤60 package lines",
    "subject not refactor/typo/docs/format/bump/version/release/revert",
)


@dataclass
class FileChange:
    path: str
    added: int
    removed: int


@dataclass
class Commit:
    repo: str
    sha: str
    parent: str
    date: str
    subject: str
    message: str
    files: list[FileChange]
    package_dir: str
    linked_issue: str | None = None
    pr_ref: str | None = None
    package_files: list[str] = field(default_factory=list)
    package_lines: int = 0


def is_support_file(path: str) -> bool:
    """Tests, docs, changelogs and CI files: allowed beside a fix, never counted or reverted."""
    return bool(TEST_PATH.search(path) or DOC_PATH.search(path) or CI_PATH.search(path))


def is_package_source(path: str, package_dir: str) -> bool:
    return path.startswith(package_dir) and path.endswith(".py") and not TEST_PATH.search(path)


def read_commits(repo: str, package_dir: str, start: date, end: date) -> list[Commit]:
    repo_dir = clone(repo, start)
    out = git(
        repo_dir,
        "log",
        "HEAD",
        "--no-merges",
        f"--since={start.isoformat()}",
        f"--until={end.isoformat()}",
        "--format=%x00%H%x1f%P%x1f%cs%x1f%s%x1f%B%x1e",
        "--numstat",
    )
    commits = []
    for chunk in out.split("\x00")[1:]:
        header, _, stats = chunk.partition("\x1e")
        sha, parents, day, subject, message = header.split("\x1f", 4)
        files = []
        for line in stats.strip().splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                added, removed, path = parts
                # Binary files report "-"; count them as zero lines.
                files.append(
                    FileChange(
                        path,
                        int(added) if added != "-" else 0,
                        int(removed) if removed != "-" else 0,
                    )
                )
        commits.append(
            Commit(
                repo=repo,
                sha=sha,
                parent=parents.split()[0] if parents else "",
                date=day,
                subject=subject.strip(),
                message=message.strip(),
                files=files,
                package_dir=package_dir,
            )
        )
    return commits


def annotate(commit: Commit) -> Commit:
    issue = ISSUE_LINK.search(commit.message)
    pr = PR_REF.search(commit.message)
    commit.linked_issue = issue.group(3) if issue else None
    commit.pr_ref = pr.group(0).strip("()") if pr else None
    package = [f for f in commit.files if is_package_source(f.path, commit.package_dir)]
    commit.package_files = [f.path for f in package]
    commit.package_lines = sum(f.added + f.removed for f in package)
    return commit


def package_scoped(commit: Commit) -> bool:
    if not commit.package_files:
        return False
    return all(f.path in commit.package_files or is_support_file(f.path) for f in commit.files)


def within_size(commit: Commit) -> bool:
    return 0 < commit.package_lines <= MAX_LINES and len(commit.package_files) <= MAX_FILES


def mine(repo: str, package_dir: str) -> tuple[list[Commit], list[int]]:
    """(surviving candidates, survivors after each filter)."""
    stage = [annotate(c) for c in read_commits(repo, package_dir, WINDOW_START, WINDOW_END)]
    counts = [len(stage)]
    for keep in (
        lambda c: bool(BUGFIX.search(c.message)),
        package_scoped,
        within_size,
        lambda c: not EXCLUDED_SUBJECT.search(c.subject),
    ):
        stage = [c for c in stage if keep(c)]
        counts.append(len(stage))
    return stage, counts


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    report: dict[str, dict[str, object]] = {}
    total = 0
    with (DATA / "candidates.jsonl").open("w") as out:
        for repo, package_dir in SELECTED.items():
            candidates, counts = mine(repo, package_dir)
            head = git(Path("evals/.repos") / repo.replace("/", "__"), "rev-parse", "HEAD").strip()
            report[repo] = {"head": head, "filters": dict(zip(FILTERS, counts, strict=True))}
            for c in sorted(candidates, key=lambda c: (c.date, c.sha)):
                out.write(json.dumps(asdict(c)) + "\n")
            total += len(candidates)
    (DATA / "mining_report.json").write_text(
        json.dumps(
            {
                "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
                "repos": report,
                "total": total,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Window {WINDOW_START} → {WINDOW_END}. Survivors after each filter:")
    print("| Repo | " + " | ".join(FILTERS) + " |")
    print("|" + "---|" * (len(FILTERS) + 1))
    for repo, r in report.items():
        print(f"| {repo} | " + " | ".join(str(v) for v in r["filters"].values()) + " |")  # type: ignore[attr-defined]
    print(f"Total candidates: {total}")


if __name__ == "__main__":
    main()
