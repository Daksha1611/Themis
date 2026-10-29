"""Warm the context caches for a repository's default branch (ADR-014's manual re-index).

    python -m app.context.reindex <owner/repo> --installation-id N

Fetches every package blob not already cached and embeds every chunk, so the next review of
that repository fetches and embeds only what changed since.
"""

import argparse
import asyncio
from pathlib import Path

from app.config import get_settings
from app.context.builder import BlobCache, _embedder, package_files, package_roots
from app.context.chunker import chunk_source
from app.github import client as gh
from app.github.auth import get_installation_token
from app.github.contents import fetch_blobs, fetch_tree


async def reindex(repo: str, installation_id: int) -> str:
    settings = get_settings()
    token = await get_installation_token(installation_id)
    response = await gh.get_client().get(f"/repos/{repo}", headers=gh.github_headers(token))
    response.raise_for_status()
    branch = response.json()["default_branch"]
    tree = await fetch_tree(token, repo, branch)
    cache = BlobCache(Path(settings.context_cache_dir) / "blobs.db")
    embedder = _embedder(settings.context_cache_dir)
    report = []
    for root in package_roots(list(tree)):
        wanted = package_files(tree, root)
        shas = sorted(set(wanted.values()))
        missing = sorted(set(shas) - set(cache.get_many(shas)))
        if missing:
            cache.put_many(await fetch_blobs(token, repo, missing))
        sources = cache.get_many(shas)
        chunks = [c for path, sha in wanted.items() for c in chunk_source(path, sources[sha])]
        embedder.encode([c.code for c in chunks])
        report.append(f"{root}: {len(wanted)} files ({len(missing)} fetched), {len(chunks)} chunks")
    await gh.close_client()
    return "\n".join(report) or "no Python package found"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo")
    parser.add_argument("--installation-id", type=int, required=True)
    args = parser.parse_args(argv)
    print(asyncio.run(reindex(args.repo, args.installation_id)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
