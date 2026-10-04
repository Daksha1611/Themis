"""Chunk Python source by function and class with tree-sitter (ADR-015).

A class becomes one chunk for its header (signature, docstring and class-level statements up to
its first method) plus one chunk per method, named `Class.method`. Top-level functions are one
chunk each; nested functions stay inside their parent. Module-level code outside definitions is
not chunked.
"""

from dataclasses import dataclass
from functools import lru_cache

import tree_sitter_python
from tree_sitter import Language, Node, Parser


@dataclass(frozen=True)
class Chunk:
    path: str
    symbol: str  # function, Class, or Class.method
    kind: str  # "function" | "class" | "method"
    start_line: int  # 1-based, inclusive
    end_line: int
    code: str


@lru_cache
def _parser() -> Parser:
    return Parser(Language(tree_sitter_python.language()))


def parse(source: bytes) -> Node:
    return _parser().parse(source).root_node


def _definition(node: Node) -> Node | None:
    """The function or class definition a top-level statement holds, through decorators."""
    if node.type == "decorated_definition":
        node = node.child_by_field_name("definition") or node
    return node if node.type in ("function_definition", "class_definition") else None


def _name(node: Node) -> str:
    name = node.child_by_field_name("name")
    return name.text.decode() if name is not None and name.text is not None else "?"


def chunk_source(path: str, source: str) -> list[Chunk]:
    data = source.encode()
    lines = source.splitlines()

    def make(node: Node, symbol: str, kind: str, end_line: int | None = None) -> Chunk:
        start = node.start_point[0] + 1
        end = end_line if end_line is not None else node.end_point[0] + 1
        return Chunk(path, symbol, kind, start, end, "\n".join(lines[start - 1 : end]))

    chunks: list[Chunk] = []
    for top in parse(data).children:
        definition = _definition(top)
        if definition is None:
            continue
        if definition.type == "function_definition":
            chunks.append(make(top, _name(definition), "function"))
            continue
        class_name = _name(definition)
        body = definition.child_by_field_name("body")
        methods = [
            (child, d)
            for child in (body.children if body is not None else [])
            if (d := _definition(child)) is not None and d.type == "function_definition"
        ]
        header_end = (
            methods[0][0].start_point[0] if methods else top.end_point[0] + 1
        )  # the line before the first method (1-based end = 0-based start of that method)
        chunks.append(make(top, class_name, "class", max(header_end, top.start_point[0] + 1)))
        for child, d in methods:
            chunks.append(make(child, f"{class_name}.{_name(d)}", "method"))
    return chunks
