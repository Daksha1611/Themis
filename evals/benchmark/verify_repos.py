"""Q20 / M3 Step 1: verify benchmark candidate repos before mining.

For each repo: clone history for the window (bare, shallow), then report bug-fix commit counts,
how many are confined to package source, linked issues, date range and distribution, and
whether the changelog has a separable "fixed" section.

    python -m evals.benchmark.verify_repos [--months 18] [--include-fallbacks]
"""

import argparse
import json
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

REPOS_DIR = Path("evals/.repos")
OUT = Path("evals/benchmark/data/repo_verification.json")
VIABLE_MIN = 40
MID_2025 = date(2025, 7, 1)

# repo → package directory (where the library's own source lives)
CANDIDATES = {
    "encode/httpx": "httpx/",
    "pallets/click": "src/click/",
    "marshmallow-code/marshmallow": "src/marshmallow/",
    "Textualize/rich": "rich/",
    "agronholm/anyio": "src/anyio/",  # the brief's "python-trio/anyio" does not exist on GitHub
}
# Q20 (decided 2026-10-02): the five repos the benchmark is built from.
SELECTED = {
    "pallets/click": "src/click/",
    "agronholm/anyio": "src/anyio/",
    "fastapi/fastapi": "fastapi/",
    "marshmallow-code/marshmallow": "src/marshmallow/",
    "Textualize/rich": "rich/",
}
FALLBACKS = {
    "encode/httpcore": "httpcore/",
    "fastapi/fastapi": "fastapi/",  # formerly tiangolo/fastapi
}

BUGFIX = re.compile(r"\b(fix(e[sd]|ing)?|bug ?fix(es)?|resolv(e[sd]?|ing))\b", re.IGNORECASE)
ISSUE_LINK = re.compile(
    r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b:?\s+(#\d+|https://github\.com/\S+/issues/\d+)",
    re.IGNORECASE,
)
PR_REF = re.compile(r"\(#\d+\)")
TEST_PATH = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$")
DOC_PATH = re.compile(r"(^|/)docs?/|\.(md|rst|txt)$|(^|/)(CHANGES|CHANGELOG|HISTORY)")
CI_PATH = re.compile(
    r"^\.github/|^\.[^/]+$|^(pyproject\.toml|setup\.(py|cfg)|tox\.ini|noxfile\.py)$"
)
FIXED_HEADING = re.compile(r"^\s*(#+\s*)?(fixed|bug ?fixes|bugfixes)\b:?\s*$", re.IGNORECASE | re.M)
CHANGELOG_NAMES = (
    "CHANGELOG.md",
    "CHANGES.md",
    "CHANGES.rst",
    "CHANGELOG.rst",
    "HISTORY.md",
    "docs/changelog.md",
    "docs/changes.rst",
    "docs/changelog.rst",
    "docs/release-notes.md",
)


@dataclass
class Report:
    repo: str
    package_dir: str
    fallback: bool
    window_start: str
    total_commits: int = 0
    bugfix_commits: int = 0
    package_scoped: int = 0  # all non-test/doc/CI files are package .py, at least one is
    package_only: int = 0  # every file touched is package .py
    with_issue_link: int = 0  # among package_scoped: "fixes #N" style link
    with_pr_ref: int = 0  # among package_scoped: "(#N)" squash-merge reference
    first_date: str | None = None
    last_date: str | None = None
    after_mid_2025: int = 0
    by_quarter: dict[str, int] = field(default_factory=dict)
    changelog: str | None = None
    changelog_fixed_section: bool = False
    viable: bool = False


def git(repo_dir: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args], check=True, capture_output=True, text=True
    ).stdout


def clone(repo: str, since: date) -> Path:
    target = REPOS_DIR / repo.replace("/", "__")
    # A month of extra history gives commits at the window edge a parent to diff against.
    shallow_since = (since - timedelta(days=31)).isoformat()
    if target.exists():
        git(target, "fetch", "--quiet", f"--shallow-since={shallow_since}", "origin")
    else:
        REPOS_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--bare",
                f"--shallow-since={shallow_since}",
                f"https://github.com/{repo}.git",
                str(target),
            ],
            check=True,
        )
    return target


def commits(repo_dir: Path, since: date) -> list[tuple[str, date, str, list[str]]]:
    """(sha, date, message, files) for non-merge commits on HEAD since `since`."""
    out = git(
        repo_dir,
        "log",
        "HEAD",
        "--no-merges",
        f"--since={since.isoformat()}",
        "--format=%x00%H%x1f%cs%x1f%B%x1e",
        "--name-only",
    )
    result = []
    for chunk in out.split("\x00")[1:]:
        header, _, files_part = chunk.partition("\x1e")
        sha, day, message = header.split("\x1f", 2)
        files = [f for f in files_part.strip().splitlines() if f]
        result.append((sha, date.fromisoformat(day), message.strip(), files))
    return result


def classify(files: list[str], package_dir: str) -> tuple[bool, bool]:
    """(package_scoped, package_only)"""
    package_py = [f for f in files if f.startswith(package_dir) and f.endswith(".py")]
    if not package_py:
        return False, False
    other = [f for f in files if f not in package_py]
    scoped = all(TEST_PATH.search(f) or DOC_PATH.search(f) or CI_PATH.search(f) for f in other)
    return scoped, not other


def check_changelog(repo_dir: Path) -> tuple[str | None, bool]:
    for name in CHANGELOG_NAMES:
        try:
            text = git(repo_dir, "show", f"HEAD:{name}")
        except subprocess.CalledProcessError:
            continue
        return name, bool(FIXED_HEADING.search(text))
    return None, False


def verify(repo: str, package_dir: str, fallback: bool, since: date) -> Report:
    repo_dir = clone(repo, since)
    report = Report(repo, package_dir, fallback, since.isoformat())
    quarters: Counter[str] = Counter()
    dates: list[date] = []
    for _sha, day, message, files in commits(repo_dir, since):
        report.total_commits += 1
        if not BUGFIX.search(message):
            continue
        report.bugfix_commits += 1
        scoped, only = classify(files, package_dir)
        report.package_only += only
        if not scoped:
            continue
        report.package_scoped += 1
        report.with_issue_link += bool(ISSUE_LINK.search(message))
        report.with_pr_ref += bool(PR_REF.search(message))
        report.after_mid_2025 += day >= MID_2025
        quarters[f"{day.year}-Q{(day.month - 1) // 3 + 1}"] += 1
        dates.append(day)
    if dates:
        report.first_date, report.last_date = min(dates).isoformat(), max(dates).isoformat()
    report.by_quarter = dict(sorted(quarters.items()))
    report.changelog, report.changelog_fixed_section = check_changelog(repo_dir)
    report.viable = report.package_scoped >= VIABLE_MIN
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--include-fallbacks", action="store_true")
    args = parser.parse_args()
    since = (datetime.now(UTC) - timedelta(days=round(args.months * 30.44))).date()

    repos = [(r, p, False) for r, p in CANDIDATES.items()]
    if args.include_fallbacks:
        repos += [(r, p, True) for r, p in FALLBACKS.items()]
    reports = [verify(repo, pkg, fb, since) for repo, pkg, fb in repos]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps([asdict(r) for r in reports], indent=2) + "\n")

    print(f"Window: {since} → today ({args.months} months). Viable: ≥{VIABLE_MIN} package-scoped.")
    print(
        "| Repo | Commits | Bug-fix msgs | Package-scoped | Package-only | Issue link | (#PR) ref"
        " | Date range | After 2025-07-01 | Changelog | 'Fixed' section | Viable |"
    )
    print("|" + "---|" * 12)
    for r in reports:
        name = f"{r.repo}{' (fallback)' if r.fallback else ''}"
        pct = f"{r.after_mid_2025} ({100 * r.after_mid_2025 // max(r.package_scoped, 1)}%)"
        print(
            f"| {name} | {r.total_commits} | {r.bugfix_commits} | {r.package_scoped} | "
            f"{r.package_only} | {r.with_issue_link} | {r.with_pr_ref} | "
            f"{r.first_date}–{r.last_date} | {pct} | {r.changelog or '—'} | "
            f"{'yes' if r.changelog_fixed_section else 'no'} | {'✅' if r.viable else '❌'} |"
        )
    print("\nPackage-scoped bug-fix commits per quarter:")
    for r in reports:
        print(f"  {r.repo:32} {r.by_quarter}")


if __name__ == "__main__":
    main()
