"""Fetch upstream evidence for benchmark cases: the PR each commit came from, its conversation,
review comments and reviews (bot comments included), and the issues it links to.

Read-only: only GET requests through the `gh` CLI. Nothing is ever posted upstream.

    python -m evals.benchmark.fetch_evidence --split dev

Writes one JSON file per case to evals/.cache/evidence/ (git-ignored).
"""

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

DATA = Path("evals/benchmark/data")
CACHE = Path("evals/.cache/evidence")
LINKED = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|refs?|see)\b:?\s+#(\d+)", re.IGNORECASE
)
BARE = re.compile(r"(?<![\w/])#(\d+)\b")
MAX_COMMENTS = 30


def get(path: str) -> Any:
    """One read-only GitHub API GET via the gh CLI."""
    out = subprocess.run(
        ["gh", "api", "--method", "GET", "-H", "Accept: application/vnd.github+json", path],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return {"error": out.stderr.strip()[:300]}
    return json.loads(out.stdout or "null")


def comments(items: Any, body_key: str = "body") -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    return [
        {
            "author": (c.get("user") or {}).get("login"),
            "bot": (c.get("user") or {}).get("type") == "Bot",
            "body": c.get(body_key) or "",
            **({"path": c["path"], "line": c.get("line")} if "path" in c else {}),
            **({"state": c["state"]} if "state" in c else {}),
        }
        for c in items[:MAX_COMMENTS]
        if (c.get(body_key) or "").strip()
    ]


def evidence(case: dict[str, Any]) -> dict[str, Any]:
    repo, sha = case["repo"], case["commit"]
    found: dict[str, Any] = {
        "case_id": case["case_id"],
        "repo": repo,
        "commit": sha,
        "pull_requests": [],
        "issues": [],
    }
    pulls = get(f"repos/{repo}/commits/{sha}/pulls")
    numbers = [p["number"] for p in pulls] if isinstance(pulls, list) else []
    if not numbers and case.get("pr_ref"):
        numbers = [int(case["pr_ref"].lstrip("#"))]
    texts = [case["message"]]
    for number in numbers[:2]:
        pr = get(f"repos/{repo}/pulls/{number}")
        if not isinstance(pr, dict) or "error" in pr:
            continue
        found["pull_requests"].append(
            {
                "number": number,
                "url": pr.get("html_url"),
                "title": pr.get("title"),
                "author": (pr.get("user") or {}).get("login"),
                "labels": [label["name"] for label in pr.get("labels", [])],
                "body": pr.get("body") or "",
                "conversation": comments(
                    get(f"repos/{repo}/issues/{number}/comments?per_page=100")
                ),
                "review_comments": comments(
                    get(f"repos/{repo}/pulls/{number}/comments?per_page=100")
                ),
                "reviews": comments(get(f"repos/{repo}/pulls/{number}/reviews?per_page=100")),
            }
        )
        texts.append(pr.get("body") or "")
    pr_numbers = set(numbers)
    linked = []
    same_repo_url = re.compile(rf"github\.com/{re.escape(repo)}/issues/(\d+)", re.IGNORECASE)
    for text in texts:
        for n in [*LINKED.findall(text), *same_repo_url.findall(text), *BARE.findall(text)]:
            if int(n) not in pr_numbers and int(n) not in linked:
                linked.append(int(n))
    for number in linked[:4]:
        issue = get(f"repos/{repo}/issues/{number}")
        if not isinstance(issue, dict) or "error" in issue:
            continue
        found["issues"].append(
            {
                "number": number,
                "url": issue.get("html_url"),
                "title": issue.get("title"),
                "is_pull_request": "pull_request" in issue,
                "labels": [label["name"] for label in issue.get("labels", [])],
                "body": issue.get("body") or "",
                "comments": comments(get(f"repos/{repo}/issues/{number}/comments?per_page=100")),
            }
        )
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=("dev",), required=True)  # holdout: not before freeze
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    cases = [json.loads(line) for line in (DATA / f"{args.split}.jsonl").read_text().splitlines()]
    for i, case in enumerate(sorted(cases, key=lambda c: c["case_id"]), 1):
        path = CACHE / f"{case['case_id']}.json"
        if path.exists():
            continue
        path.write_text(json.dumps(evidence(case), indent=1))
        print(f"{i}/{len(cases)} {case['case_id']} {case['repo']}", flush=True)


if __name__ == "__main__":
    main()
