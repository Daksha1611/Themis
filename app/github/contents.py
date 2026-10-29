"""Read-only repository contents for the context builder (M4): the file tree at a commit, and
blob sources. Shapes verified against the live API on 2026-10-28 (git trees and git blobs)."""

import asyncio
import base64

from app.github import client as gh


async def fetch_tree(token: str, repo_full_name: str, sha: str) -> dict[str, str]:
    """path -> blob SHA for every file at `sha` (one recursive tree call)."""
    response = await gh.get_client().get(
        f"/repos/{repo_full_name}/git/trees/{sha}",
        params={"recursive": "1"},
        headers=gh.github_headers(token),
    )
    gh.raise_if_rate_limited(response, f"tree of {repo_full_name}@{sha[:7]}")
    response.raise_for_status()
    return {t["path"]: t["sha"] for t in response.json()["tree"] if t["type"] == "blob"}


async def fetch_blobs(
    token: str, repo_full_name: str, shas: list[str], concurrency: int = 8
) -> dict[str, str]:
    """blob SHA -> source text (UTF-8, undecodable bytes replaced)."""
    limit = asyncio.Semaphore(concurrency)

    async def one(sha: str) -> tuple[str, str]:
        async with limit:
            response = await gh.get_client().get(
                f"/repos/{repo_full_name}/git/blobs/{sha}", headers=gh.github_headers(token)
            )
        gh.raise_if_rate_limited(response, f"blob {sha[:7]} of {repo_full_name}")
        response.raise_for_status()
        data = response.json()
        raw = base64.b64decode(data["content"]) if data["encoding"] == "base64" else b""
        return sha, raw.decode("utf-8", "replace")

    return dict(await asyncio.gather(*(one(sha) for sha in shas)))


async def fetch_base_sha(token: str, repo_full_name: str, pr_number: int) -> str:
    response = await gh.get_client().get(
        f"/repos/{repo_full_name}/pulls/{pr_number}", headers=gh.github_headers(token)
    )
    gh.raise_if_rate_limited(response, f"{repo_full_name}#{pr_number}")
    response.raise_for_status()
    return str(response.json()["base"]["sha"])
