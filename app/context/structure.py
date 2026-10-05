"""Structural lookup over a package snapshot (ADR-028): definitions of names a diff references,
and callers of functions a diff changes. tree-sitter plus import analysis; no type inference.

Resolution of a referenced name, in order:
- `self.x` / `cls.x`: method `x` of the enclosing class (then of its in-package base classes).
- `alias.x` where `alias` is an imported module: definition `x` in that module.
- bare `x`: a definition in the same module, else an imported name (aliases and relative
  imports followed, one re-export hop).
- `obj.x` on any other object: the type is unknown, so every method named `x` in the package is
  a candidate. Up to MAX_CANDIDATES are included and marked ambiguous; more are unresolved.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from tree_sitter import Node

from app.context.chunker import Chunk, chunk_source, parse

MAX_CANDIDATES = 3
SELF_NAMES = ("self", "cls")


@dataclass
class Reference:
    name: str
    kind: str  # "name" | "self" | "module_attr" | "attr"
    owner: str | None = None  # module alias for module_attr


@dataclass
class Resolution:
    chunks: list[Chunk] = field(default_factory=list)
    ambiguous: bool = False
    reason: str = ""  # why nothing was resolved


class PackageIndex:
    """Definitions, imports and parse trees of every file in a package snapshot."""

    def __init__(self, files: dict[str, str], package_root: str) -> None:
        self.files = files
        parent = (
            package_root.rstrip("/").rsplit("/", 1)[0] + "/"
            if "/" in package_root.rstrip("/")
            else ""
        )
        self.package = package_root.rstrip("/").rsplit("/", 1)[-1]
        self.module_of: dict[str, str] = {}
        self.path_of: dict[str, str] = {}
        for path in files:
            dotted = path[len(parent) : -3].replace("/", ".")
            dotted = dotted.removesuffix(".__init__")
            self.module_of[path], self.path_of[dotted] = dotted, path
        self.trees: dict[str, Node] = {}
        self.chunks: dict[str, list[Chunk]] = {}
        self.top: dict[str, dict[str, Chunk]] = {}  # module -> name -> top-level def
        self.methods: dict[tuple[str, str], dict[str, Chunk]] = {}  # (path, class) -> methods
        self.methods_by_name: dict[str, list[Chunk]] = defaultdict(list)
        self.bases: dict[tuple[str, str], list[str]] = {}
        self.imports: dict[str, dict[str, tuple[str, str | None]]] = {}
        for path, source in files.items():
            self._load(path, source)

    def _load(self, path: str, source: str) -> None:
        tree = parse(source.encode())
        self.trees[path] = tree
        chunks = chunk_source(path, source)
        self.chunks[path] = chunks
        module = self.module_of[path]
        self.top[module] = {}
        for chunk in chunks:
            if chunk.kind in ("function", "class"):
                self.top[module][chunk.symbol] = chunk
            else:
                cls, name = chunk.symbol.split(".", 1)
                self.methods.setdefault((path, cls), {})[name] = chunk
                self.methods_by_name[name].append(chunk)
        self.imports[path] = self._imports(path, tree)
        for node in tree.children:
            definition = node.child_by_field_name("definition") or node
            if definition.type == "class_definition":
                args = definition.child_by_field_name("superclasses")
                names = [
                    _text(a).rsplit(".", 1)[-1]
                    for a in (args.named_children if args is not None else [])
                ]
                self.bases[(path, _text(definition.child_by_field_name("name")))] = names

    def _resolve_module(self, path: str, dotted: str, level: int) -> str:
        if level == 0:
            return dotted
        base = self.module_of[path].split(".")
        if not path.endswith("__init__.py"):
            base = base[:-1]
        base = base[: len(base) - (level - 1)] if level > 1 else base
        return ".".join([*base, dotted] if dotted else base)

    def _imports(self, path: str, tree: Node) -> dict[str, tuple[str, str | None]]:
        """alias -> (module, name) for `from m import name as alias`; (module, None) for
        `import m as alias`. Only imports in this package are kept."""
        table: dict[str, tuple[str, str | None]] = {}
        for node in tree.children:
            if node.type == "import_statement":
                for item in node.named_children:
                    target = (
                        item.child_by_field_name("name") if item.type == "aliased_import" else item
                    )
                    alias = (
                        item.child_by_field_name("alias") if item.type == "aliased_import" else None
                    )
                    dotted = _text(target)
                    if dotted.split(".")[0] == self.package:
                        table[_text(alias) if alias else dotted.split(".")[0]] = (dotted, None)
            elif node.type == "import_from_statement":
                module_node = node.child_by_field_name("module_name")
                raw = _text(module_node)
                level = len(raw) - len(raw.lstrip("."))
                module = self._resolve_module(path, raw.lstrip("."), level)
                if module.split(".")[0] != self.package:
                    continue
                for item in node.children_by_field_name("name"):
                    target = (
                        item.child_by_field_name("name") if item.type == "aliased_import" else item
                    )
                    alias = (
                        item.child_by_field_name("alias") if item.type == "aliased_import" else None
                    )
                    name = _text(target)
                    if f"{module}.{name}" in self.path_of:  # `from pkg import submodule`
                        table[_text(alias) if alias else name] = (f"{module}.{name}", None)
                    else:
                        table[_text(alias) if alias else name] = (module, name)
        return table

    def enclosing_class(self, path: str, line: int) -> str | None:
        for chunk in self.chunks.get(path, []):
            if chunk.kind == "method" and chunk.start_line <= line <= chunk.end_line:
                return chunk.symbol.split(".", 1)[0]
            if chunk.kind == "class" and chunk.start_line <= line <= chunk.end_line:
                return chunk.symbol
        return None

    def enclosing_chunk(self, path: str, line: int) -> Chunk | None:
        inside = [c for c in self.chunks.get(path, []) if c.start_line <= line <= c.end_line]
        return min(inside, key=lambda c: c.end_line - c.start_line) if inside else None

    def _lookup(self, module: str, name: str, hops: int = 1) -> Chunk | None:
        chunk = self.top.get(module, {}).get(name)
        if chunk is not None or hops == 0:
            return chunk
        source = self.path_of.get(module)
        target = self.imports.get(source, {}).get(name) if source else None
        if target and target[1]:  # re-exported from another module
            return self._lookup(target[0], target[1], hops - 1)
        return None

    def _method(self, path: str, cls: str, name: str, depth: int = 2) -> Chunk | None:
        found = self.methods.get((path, cls), {}).get(name)
        if found is not None or depth == 0:
            return found
        for base in self.bases.get((path, cls), []):
            base_chunk = self._lookup(self.module_of[path], base) or self._imported(path, base)
            if base_chunk is not None and base_chunk.kind == "class":
                hit = self._method(base_chunk.path, base_chunk.symbol, name, depth - 1)
                if hit is not None:
                    return hit
        return None

    def _imported(self, path: str, name: str) -> Chunk | None:
        target = self.imports.get(path, {}).get(name)
        if target is None or target[1] is None:
            return None
        return self._lookup(target[0], target[1])

    def resolve(self, path: str, line: int, ref: Reference) -> Resolution:
        if ref.kind == "self":
            cls = self.enclosing_class(path, line)
            if cls is None:
                return Resolution(reason="self/cls outside a class")
            chunk = self._method(path, cls, ref.name)
            if chunk is not None:
                return Resolution([chunk])
            return Resolution(reason="self attribute not a method of the class or its bases")
        if ref.kind == "module_attr" and ref.owner is not None:
            target = self.imports.get(path, {}).get(ref.owner)
            if target is not None and target[1] is None:
                chunk = self._lookup(target[0], ref.name)
                if chunk is not None:
                    return Resolution([chunk])
            return Resolution(reason="attribute of an imported module, not defined there")
        if ref.kind == "name":
            chunk = self._lookup(self.module_of[path], ref.name, hops=0) or self._imported(
                path, ref.name
            )
            if chunk is not None:
                return Resolution([chunk])
            return Resolution(reason="name not bound to a package definition here")
        candidates = self.methods_by_name.get(ref.name, [])
        if 0 < len(candidates) <= MAX_CANDIDATES:
            return Resolution(list(candidates), ambiguous=len(candidates) > 1)
        if not candidates:
            return Resolution(reason="attribute with no method of that name in the package")
        return Resolution(reason="attribute on an object of unknown type (too many candidates)")

    def call_sites(self, name: str) -> list[tuple[str, int]]:
        """(path, line) of every call in the package whose callee's final name is `name`."""
        sites: list[tuple[str, int]] = []
        for path, tree in self.trees.items():
            for node in _walk(tree):
                if node.type == "call":
                    callee = node.child_by_field_name("function")
                    if callee is not None and _final_name(callee) == name:
                        sites.append((path, node.start_point[0] + 1))
        return sites


def _text(node: Node | None) -> str:
    return node.text.decode() if node is not None and node.text is not None else ""


def _walk(node: Node) -> list[Node]:
    out, stack = [], [node]
    while stack:
        n = stack.pop()
        out.append(n)
        stack.extend(n.children)
    return out


def _final_name(node: Node) -> str:
    if node.type == "identifier":
        return _text(node)
    if node.type == "attribute":
        return _text(node.child_by_field_name("attribute"))
    return ""


def references(tree: Node, lines: set[int] | None, imported_modules: set[str]) -> list[Reference]:
    """References in the tree (optionally only on the given 1-based lines): bare names,
    `self.x`/`cls.x`, `module.x` through an imported module, and `obj.x` on other objects."""
    refs: list[Reference] = []
    seen: set[tuple[str, str, str | None]] = set()
    for node in _walk(tree):
        if lines is not None and node.start_point[0] + 1 not in lines:
            continue
        ref: Reference | None = None
        if node.type == "attribute":
            obj, attr = node.child_by_field_name("object"), node.child_by_field_name("attribute")
            name = _text(attr)
            if obj is not None and obj.type == "identifier":
                owner = _text(obj)
                if owner in SELF_NAMES:
                    ref = Reference(name, "self")
                elif owner in imported_modules:
                    ref = Reference(name, "module_attr", owner)
                else:
                    ref = Reference(name, "attr")
            elif name:
                ref = Reference(name, "attr")
        elif node.type == "identifier":
            parent = node.parent
            if parent is not None and parent.type == "attribute":
                continue  # handled as part of the attribute
            ref = Reference(_text(node), "name")
        if ref is not None and (ref.name, ref.kind, ref.owner) not in seen:
            seen.add((ref.name, ref.kind, ref.owner))
            refs.append(ref)
    return refs
