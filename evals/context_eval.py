"""Retrieval quality of the M4 context builder, with no LLM calls (ADR-027).

    python -m evals.context_eval --split dev [--budgets 1000,2000,4000] [--limit N]

For every scored case: materialise the fix commit's package-source tree (no tests, docs,
changelog or CI files), chunk it, embed through the content-hash cache, index it in an
in-memory Qdrant collection, and retrieve context for the case's diff at each token budget.

Metric: symbol-definition recall. The functions, methods and classes referenced in the diff's
changed lines (identifiers from the tree-sitter parse: removed lines in the fix-commit file,
added lines as a snippet) that have a definition in the snapshot outside the diff's own changed
region are the targets. A target is retrieved at budget B if any of its definitions is among
the chunks retrieved within B tokens. Recall is pooled over (case, name) pairs with a Wilson
interval, and reported per repo and per category.
"""

import argparse
import json
import re
import subprocess
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient

from app.context.chunker import Chunk, chunk_source, parse
from app.context.embeddings import CachedEmbedder, EmbeddingCache, SentenceTransformerEmbedder
from app.context.index import HybridIndex
from app.context.retriever import count_tokens, hunks, retrieve, structural
from app.context.structure import PackageIndex
from evals.benchmark.label import LABELS, load_labels
from evals.benchmark.verify_repos import SELECTED
from evals.metrics import rate
from evals.runner import scored_cases

REPOS = Path("evals/.repos")
EMBEDDING_CACHE = Path("evals/.cache/embeddings.db")
RESULTS = Path("evals/results")
VAULT_RESULTS = Path("docs/vault/08 Results")
BUDGETS = (1000, 2000, 4000)
# Never indexed (ADR-027): tests, docs, changelogs, CI. Applied on top of the package root.
EXCLUDED = re.compile(
    r"(^|/)(tests?|testing|docs?|\.github|\.circleci)/"
    r"|(^|/)(test_[^/]*|[^/]*_test|conftest)\.py$"
    r"|(^|/)(CHANGE|HISTORY|NEWS)",
    re.IGNORECASE,
)
HUNK_NEW = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
HUNK_OLD = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")


def git(repo_dir: Path, *args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args], input=data, capture_output=True, check=True
    ).stdout


def snapshot(repo: str, commit: str) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Python files under the package root at `commit`: path -> (blob SHA, source). Also the
    package paths skipped by the exclusion rule."""
    repo_dir = REPOS / repo.replace("/", "__")
    listing = git(repo_dir, "ls-tree", "-r", commit, "--", SELECTED[repo]).decode()
    blobs: dict[str, str] = {}
    skipped: list[str] = []
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        if not path.endswith(".py"):
            continue
        if EXCLUDED.search(path):
            skipped.append(path)
            continue
        blobs[path] = meta.split()[2]
    batch = git(repo_dir, "cat-file", "--batch", data="\n".join(blobs.values()).encode() + b"\n")
    sources: dict[str, str] = {}
    offset = 0
    for blob in blobs.values():
        header_end = batch.index(b"\n", offset)
        size = int(batch[offset:header_end].split()[2])
        sources[blob] = batch[header_end + 1 : header_end + 1 + size].decode("utf-8", "replace")
        offset = header_end + 1 + size + 1
    return {path: (blob, sources[blob]) for path, blob in blobs.items()}, skipped


def identifiers(node: Any, lines: set[int] | None = None) -> set[str]:
    """Identifier names in the parse tree, optionally only on the given 1-based lines."""
    found: set[str] = set()
    stack = [node]
    while stack:
        n = stack.pop()
        if n.type == "identifier" and (lines is None or n.start_point[0] + 1 in lines):
            found.add(n.text.decode())
        stack.extend(n.children)
    return found


def referenced(diff: str, files: dict[str, tuple[str, str]]) -> set[str]:
    """Names referenced on the diff's changed lines: removed lines located in the fix-commit
    file (old-side line numbers), added lines parsed as a snippet."""
    removed: dict[str, set[int]] = defaultdict(set)
    added: list[str] = []
    path: str | None = None
    old = 0
    for raw in diff.splitlines():
        if raw.startswith("--- "):
            path = raw[6:] if raw.startswith("--- a/") else None
            continue
        if raw.startswith(("+++ ", "diff --git", "index ")):
            continue
        if match := HUNK_OLD.match(raw):
            old = int(match.group(1))
            continue
        if raw.startswith("-"):
            if path:
                removed[path].add(old)
            old += 1
        elif raw.startswith("+"):
            added.append(raw[1:])
        elif raw.startswith(" "):
            old += 1
    names: set[str] = set()
    for file, lines in removed.items():
        if file in files:
            names |= identifiers(parse(files[file][1].encode()), lines)
    if added:
        names |= identifiers(parse(dedent_lines(added).encode()))
    return names


def dedent_lines(lines: list[str]) -> str:
    indents = [len(x) - len(x.lstrip()) for x in lines if x.strip()]
    cut = min(indents) if indents else 0
    return "\n".join(x[cut:] for x in lines)


def short(symbol: str) -> str:
    return symbol.rsplit(".", 1)[-1]


def evaluate_case(
    case: dict[str, Any],
    embedder: CachedEmbedder,
    chunk_cache: dict[str, list[Chunk]],
    budgets: tuple[int, ...],
) -> dict[str, Any]:
    started = time.monotonic()
    files, skipped = snapshot(case["repo"], case["commit"])
    chunks: list[Chunk] = []
    for path, (blob, source) in files.items():
        if blob not in chunk_cache:
            chunk_cache[blob] = chunk_source(path, source)
        chunks += [
            c if c.path == path else Chunk(path, c.symbol, c.kind, c.start_line, c.end_line, c.code)
            for c in chunk_cache[blob]
        ]
    index = HybridIndex(QdrantClient(":memory:"), "snapshot", embedder)
    index.add(chunks)
    structure = PackageIndex({p: src for p, (_, src) in files.items()}, SELECTED[case["repo"]])
    index_seconds = time.monotonic() - started
    found = structural(structure, case["diff"])

    regions = [(p, s, e) for p, s, e, _ in hunks(case["diff"])]
    outside = [
        c
        for c in chunks
        if not any(c.path == p and c.start_line <= e and c.end_line >= s for p, s, e in regions)
    ]
    defined = {short(c.symbol) for c in outside}
    targets = sorted(referenced(case["diff"], files) & defined)
    resolved = {ref.name for _, ref, res in found.resolutions if res.chunks}
    reasons: dict[str, str] = {}
    for _, ref, res in found.resolutions:
        if not res.chunks and ref.name not in reasons:
            reasons[ref.name] = res.reason
    # ground truth for caller coverage: every call site of a changed function outside the diff
    changed = {f.symbol.rsplit(".", 1)[-1] for f in found.changed_functions}
    call_sites = sorted(
        {
            (path, line)
            for name in changed
            for path, line in structure.call_sites(name)
            if not any(path == p and s <= line <= e for p, s, e in regions)
        }
    )
    per_budget: dict[str, Any] = {}
    leaks: list[str] = []
    for budget in budgets:
        context = retrieve(index, case["diff"], budget, structure=structure)
        got = {short(c.symbol) for c in context.related_chunks}
        leaks += [c.path for c in context.related_chunks if EXCLUDED.search(c.path)]
        spans = [(c.path, c.start_line, c.end_line) for c in context.related_chunks]
        misses = {}
        for t in targets:
            if t in got:
                continue
            if t in resolved:
                misses[t] = "resolved, but did not fit the budget"
            else:
                misses[t] = reasons.get(
                    t, "not a resolvable reference (keyword argument, import name or string)"
                )
        composition: dict[str, int] = defaultdict(int)
        for c in context.related_chunks:
            composition[c.source] += c.tokens
        per_budget[str(budget)] = {
            "hits": [t for t in targets if t in got],
            "misses": misses,
            "chunks": len(context.related_chunks),
            "tokens": context.token_budget_used,
            "composition": dict(composition),
            "call_sites_covered": sum(
                any(p == path and s <= line <= e for p, s, e in spans) for path, line in call_sites
            ),
        }
    return {
        "case_id": case["case_id"],
        "repo": case["repo"],
        "kind": case["kind"],
        "files_indexed": len(files),
        "chunks_indexed": len(chunks),
        "excluded_paths": skipped,
        "indexed_excluded": [p for p in files if EXCLUDED.search(p)],
        "index_seconds": round(index_seconds, 2),
        "targets": targets,
        "changed_functions": sorted(changed),
        "call_sites": len(call_sites),
        "budgets": per_budget,
        "leaks": sorted(set(leaks)),
    }


def context_block_tokens(cases: list[dict[str, Any]], budget: int) -> dict[str, int]:
    """Tokens a retrieved-context block would add to each case's prompt at `budget`: the chunks
    plus one header line per chunk (`# path:start-end symbol (reason)`). The final rendering is
    decided when context is wired in; this is the estimate the dry run uses."""
    embedder = CachedEmbedder(SentenceTransformerEmbedder(), EmbeddingCache(EMBEDDING_CACHE))
    out: dict[str, int] = {}
    chunk_cache: dict[str, list[Chunk]] = {}
    for case in cases:
        files, _ = snapshot(case["repo"], case["commit"])
        chunks = [
            c
            for path, (blob, source) in files.items()
            for c in chunk_cache.setdefault(blob, chunk_source(path, source))
        ]
        index = HybridIndex(QdrantClient(":memory:"), "snapshot", embedder)
        index.add(chunks)
        structure = PackageIndex({p: src for p, (_, src) in files.items()}, SELECTED[case["repo"]])
        context = retrieve(index, case["diff"], budget, structure=structure)
        headers = sum(
            count_tokens(f"# {c.path}:{c.start_line}-{c.end_line} {c.symbol} ({c.reason})")
            for c in context.related_chunks
        )
        out[case["case_id"]] = context.token_budget_used + headers
    return out


def summarize(
    results: list[dict[str, Any]], categories: dict[str, str], budgets: tuple[int, ...]
) -> dict[str, Any]:
    def pooled(subset: list[dict[str, Any]], budget: int) -> dict[str, Any]:
        hits = sum(len(r["budgets"][str(budget)]["hits"]) for r in subset)
        return rate(hits, sum(len(r["targets"]) for r in subset))

    groups: dict[str, dict[str, list[dict[str, Any]]]] = {
        "repo": defaultdict(list),
        "category": defaultdict(list),
    }
    for r in results:
        groups["repo"][r["repo"]].append(r)
        groups["category"][categories.get(r["case_id"], r["kind"])].append(r)

    def callers(subset: list[dict[str, Any]], budget: int) -> dict[str, Any]:
        covered = sum(r["budgets"][str(budget)]["call_sites_covered"] for r in subset)
        return rate(covered, sum(r["call_sites"] for r in subset))

    def composition(budget: int) -> dict[str, float]:
        shares: dict[str, list[float]] = defaultdict(list)
        for r in results:
            b = r["budgets"][str(budget)]
            if b["tokens"]:
                for source in ("definition", "caller", "semantic"):
                    shares[source].append(b["composition"].get(source, 0) / budget)
        return {k: sum(v) / len(v) for k, v in shares.items()} if shares else {}

    def miss_reasons(budget: int) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for r in results:
            for reason in r["budgets"][str(budget)]["misses"].values():
                counts[reason] += 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    return {
        "caller_coverage": {str(b): callers(results, b) for b in budgets},
        "caller_cases": sum(bool(r["call_sites"]) for r in results),
        "composition": {str(b): composition(b) for b in budgets},
        "miss_reasons": {str(b): miss_reasons(b) for b in budgets},
        "falsification_split": {
            "with_targets": sorted(r["case_id"] for r in results if r["targets"]),
            "without_targets": sorted(r["case_id"] for r in results if not r["targets"]),
        },
        "cases": len(results),
        "cases_with_targets": sum(bool(r["targets"]) for r in results),
        "targets": sum(len(r["targets"]) for r in results),
        "overall": {str(b): pooled(results, b) for b in budgets},
        "by_repo": {
            g: {str(b): pooled(m, b) for b in budgets} for g, m in sorted(groups["repo"].items())
        },
        "by_category": {
            g: {str(b): pooled(m, b) for b in budgets}
            for g, m in sorted(groups["category"].items())
        },
        "leakage": {
            "retrieved_from_excluded_paths": sum(len(r["leaks"]) for r in results),
            "indexed_from_excluded_paths": sum(len(r["indexed_excluded"]) for r in results),
            "package_paths_excluded_by_rule": sorted(
                {p for r in results for p in r["excluded_paths"]}
            ),
        },
        "indexing": {
            "mean_seconds": sum(r["index_seconds"] for r in results) / max(len(results), 1),
            "max_seconds": max((r["index_seconds"] for r in results), default=0.0),
            "mean_chunks": sum(r["chunks_indexed"] for r in results) / max(len(results), 1),
        },
    }


def render(
    s: dict[str, Any],
    budgets: tuple[int, ...],
    meta: dict[str, Any],
    previous: dict[str, Any] | None = None,
) -> str:
    def cell(r: dict[str, Any]) -> str:
        if not r["n"]:
            return "n/a"
        return f"{r['rate']:.1%} ({r['k']}/{r['n']}; {r['low']:.1%}–{r['high']:.1%})"

    head = "| Group | " + " | ".join(f"{b} tokens" for b in budgets) + " |"
    sep = "|---|" + "---|" * len(budgets)
    lk = s["leakage"]
    out = [
        "# Context retrieval: dev split (structural lookup + hybrid)",
        "",
        "Retrieval of the M4 context builder with structural lookup ([[ADR-028 Structural lookup "
        "plus hybrid search]], [[ADR-027 Eval-time repo context]]), measured with **no LLM "
        "calls**. Not wired into the review path.",
        "",
        f"- Generated {meta['generated']} by `python -m evals.context_eval --split dev` at git "
        f"`{meta['git_sha'][:7]}`; embedder `{meta['embedder']}`; in-memory Qdrant",
        f"- Cases: {s['cases']} scored dev cases; {s['cases_with_targets']} reference at least "
        f"one external definition ({s['targets']} targets in all); {s['caller_cases']} change a "
        "function that has in-package call sites",
        "",
        "> **Symbol-definition recall is now a resolution-coverage check, not evidence of "
        "usefulness.** Structural lookup retrieves definitions of referenced names by "
        "construction, so a high number shows the resolver and the budget work. Whether context "
        "helps the review is measured only by the M4 ablation (v2 vs v2 + context, McNemar, "
        "falsification split; [[Eval Harness]]).",
        "",
        "## Symbol-definition recall (resolution coverage)",
        "",
        head,
        sep,
    ]
    if previous:
        out.append(
            "| Pure hybrid (2026-10-04, superseded) | "
            + " | ".join(cell(previous["overall"][str(b)]) for b in budgets)
            + " |"
        )
    out.append(
        "| **Structural + hybrid** | "
        + " | ".join(cell(s["overall"][str(b)]) for b in budgets)
        + " |"
    )
    out += [
        "",
        "By repo (structural + hybrid):",
        "",
        head,
        sep,
        *(
            f"| {g} | " + " | ".join(cell(v[str(b)]) for b in budgets) + " |"
            for g, v in s["by_repo"].items()
        ),
        "",
        f"## Remaining misses at {budgets[-1]} tokens",
        "",
        "| Reason | Targets |",
        "|---|---|",
        *(f"| {reason} | {n} |" for reason, n in s["miss_reasons"][str(budgets[-1])].items()),
        "",
        "## Caller coverage",
        "",
        "For diffs that modify a function: the share of its in-package call sites (matched by "
        "the callee's name, outside the diff) whose enclosing function or method is in the "
        "context.",
        "",
        head,
        sep,
        "| Call sites | " + " | ".join(cell(s["caller_coverage"][str(b)]) for b in budgets) + " |",
        "",
        "## Budget composition",
        "",
        "Average share of the token budget per source (cases with any context):",
        "",
        "| Source | " + " | ".join(f"{b} tokens" for b in budgets) + " |",
        sep,
        *(
            f"| {source} | "
            + " | ".join(f"{s['composition'][str(b)].get(source, 0):.1%}" for b in budgets)
            + " |"
            for source in ("definition", "caller", "semantic")
        ),
        "",
        "## By category (structural + hybrid)",
        "",
        head,
        sep,
        *(
            f"| {g} | " + " | ".join(cell(v[str(b)]) for b in budgets) + " |"
            for g, v in s["by_category"].items()
        ),
        "",
        "## Leakage check",
        "",
        f"- Chunks retrieved from test, doc, changelog or CI paths, across all cases and budgets: "
        f"**{lk['retrieved_from_excluded_paths']}**",
        f"- Files indexed from such paths: **{lk['indexed_from_excluded_paths']}**",
        "",
        "## Indexing",
        "",
        f"- Mean {s['indexing']['mean_seconds']:.1f} s per case snapshot (max "
        f"{s['indexing']['max_seconds']:.1f} s), mean {s['indexing']['mean_chunks']:.0f} chunks",
        f"- Embedding cache: {meta['cache_hits']} hits, {meta['cache_misses']} misses "
        f"(hit rate {meta['cache_hit_rate']:.1%}); total wall time {meta['seconds']:.0f} s",
        "",
        "## Caveats",
        "",
        "- A referenced name counts as retrieved if any definition with that name is retrieved; "
        "names defined several times can match a different definition.",
        "- Call sites are matched by the callee's name, without type information, so a method "
        "name shared by several classes yields callers of all of them (marked ambiguous).",
        "- Dense embeddings truncate chunks at 256 tokens; sparse vectors cover the whole chunk.",
    ]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=("dev",), default="dev")
    parser.add_argument("--budgets", default=",".join(map(str, BUDGETS)))
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    budgets = tuple(int(b) for b in args.budgets.split(","))
    labels = load_labels(LABELS)
    cases = scored_cases(args.split, labels)[: args.limit]
    categories = {cid: r["category"] for cid, r in labels.items() if r.get("valid")}
    embedder = CachedEmbedder(SentenceTransformerEmbedder(), EmbeddingCache(EMBEDDING_CACHE))
    chunk_cache: dict[str, list[Chunk]] = {}
    started = time.monotonic()
    results = []
    for n, case in enumerate(cases, 1):
        results.append(evaluate_case(case, embedder, chunk_cache, budgets))
        print(
            f"{n}/{len(cases)} {case['case_id']} targets={len(results[-1]['targets'])}", flush=True
        )
    summary = summarize(results, categories, budgets)
    lookups = embedder.hits + embedder.misses
    meta: dict[str, Any] = {
        "generated": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "embedder": embedder.name,
        "cache_hits": embedder.hits,
        "cache_misses": embedder.misses,
        "cache_hit_rate": embedder.hits / lookups if lookups else 0.0,
        "seconds": time.monotonic() - started,
    }
    stamp = meta["generated"][:10]
    out_dir = RESULTS / f"context-{args.split}-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in results))
    (out_dir / "summary.json").write_text(json.dumps({**meta, **summary}, indent=1) + "\n")
    name = f"context-retrieval-{args.split}-{stamp}"
    front = (
        f"---\nname: {name}\n"
        'description: "Resolution coverage, caller coverage and budget composition of the M4 '
        f"context builder (structural lookup + hybrid) on the {args.split} split, with the "
        'leakage check; no LLM calls."\ntype: reliability\nstatus: done\n'
        "tags: [reliability, results]\nrelated:\n"
        '  - "[[ADR-028 Structural lookup plus hybrid search]]"\n'
        '  - "[[ADR-027 Eval-time repo context]]"\n  - "[[Context Builder]]"\n'
        '  - "[[Eval Harness]]"\n---\n\n'
    )
    previous_path = RESULTS / "context-dev-2026-10-04" / "summary.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else None
    if args.limit is None:
        (VAULT_RESULTS / f"{name}.md").write_text(front + render(summary, budgets, meta, previous))
    print(json.dumps(summary["overall"], indent=1))
    print(json.dumps(summary["leakage"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
