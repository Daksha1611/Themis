"""Mechanical consistency checks for the vault (docs/vault/), docs/flow.md and the code.

Exits 1 and prints every failure when any check fails, so vault drift fails CI like a lint
error. Standard library only: CI runs it without installing the project.

    python scripts/check_vault.py [repo_root]

Checks:
1. Call graph: every function in docs/flow.md's call graph index exists at the stated file,
   and every function in app/ has a row. Exempt by rule: dunder methods, Pydantic validators,
   everything under app/storage/migrations/ (revision upgrade/downgrade and env.py internals),
   and private leaf helpers (a "_name" function that calls no function defined in app/).
2. Every [[wikilink]] in a vault note resolves to an existing note or file.
3. ADR numbers are unique, with no gaps.
4. Open-question numbers are unique.
5. Every note has valid frontmatter: name = filename stem, non-empty description, a known type,
   and a status valid for that type (see the Glossary note).
6. No note is an orphan (zero inbound links), except 00 Index and 00 Brief.
7. Every package in pyproject.toml has a stack note, whose version names the pinned version.
   An empty version is allowed only when the note's status is planned (not installed yet).
"""

import ast
import re
import sys
import tomllib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Mirrors the status table in docs/vault/01 Project/Glossary.md.
STATUSES = {
    "project": {"planned", "in-progress", "done"},
    "component": {"planned", "in-progress", "done"},
    "reliability": {"planned", "in-progress", "done"},
    "progress": {"planned", "in-progress", "done"},
    "tech": {"planned", "in-progress", "done"},
    "risk": {"planned", "in-progress", "done"},
    "decision": {"accepted", "superseded"},
}
ORPHAN_EXEMPT = {"00 Index", "00 Brief"}
VALIDATOR_DECORATORS = {"field_validator", "model_validator", "validator", "root_validator"}
EXEMPT_CODE_DIRS = ("app/storage/migrations/",)

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FENCED_CODE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
FUNCTION_REF = re.compile(r"^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\(\)$")
ADR_FILE = re.compile(r"^ADR-(\d{3}) .+\.md$")
QUESTION_ENTRY = re.compile(r"^[-*] \*\*Q(\d+[a-z]?)\b", re.M)
NUMBERED_ITEM = re.compile(r"^\d+[a-z]?\. ", re.M)

Frontmatter = dict[str, str | list[str]]


class FrontmatterError(ValueError):
    pass


@dataclass
class Note:
    path: Path
    rel: str  # path relative to the vault, without ".md"
    text: str
    frontmatter: Frontmatter | None
    frontmatter_error: str | None
    links: list[str] = field(default_factory=list)

    @property
    def stem(self) -> str:
        return self.path.stem


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].replace('\\"', '"')
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(text: str) -> Frontmatter | None:
    """Parse the YAML subset the vault uses: scalars, [inline, lists] and `  - item` lists."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 3)
    if end == -1:
        raise FrontmatterError("frontmatter is not closed with ---")
    data: Frontmatter = {}
    list_key: str | None = None
    for line in text[4:end].split("\n"):
        if not line.strip():
            continue
        if line.startswith(("  - ", "- ")):
            current = data.get(list_key) if list_key else None
            if not isinstance(current, list):
                raise FrontmatterError(f"list item outside a list: {line.strip()!r}")
            current.append(_unquote(line.split("- ", 1)[1].strip()))
            continue
        key, sep, value = line.partition(":")
        if not sep or not key or key != key.strip() or " " in key:
            raise FrontmatterError(f"unparseable line: {line!r}")
        if key in data:
            raise FrontmatterError(f"duplicate key: {key}")
        value = value.strip()
        if value == "":
            data[key] = []
            list_key = key
        elif value.startswith("[") and value.endswith("]"):
            data[key] = [_unquote(v.strip()) for v in value[1:-1].split(",") if v.strip()]
            list_key = None
        else:
            data[key] = _unquote(value)
            list_key = None
    return data


def load_notes(vault: Path) -> list[Note]:
    notes = []
    for path in sorted(vault.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        frontmatter: Frontmatter | None = None
        error: str | None = None
        try:
            frontmatter = parse_frontmatter(text)
        except FrontmatterError as exc:
            error = str(exc)
        searchable = INLINE_CODE.sub("", FENCED_CODE.sub("", text))
        notes.append(
            Note(
                path=path,
                rel=path.relative_to(vault).with_suffix("").as_posix(),
                text=text,
                frontmatter=frontmatter,
                frontmatter_error=error,
                links=[m.group(1).strip() for m in WIKILINK.finditer(searchable)],
            )
        )
    return notes


def _resolver(notes: list[Note], vault: Path) -> dict[str, str]:
    """Map every way a link can name a note (stem or vault-relative path) to its `rel`."""
    targets: dict[str, str] = {}
    for note in notes:
        targets.setdefault(note.stem, note.rel)
        targets[note.rel] = note.rel
    for other in vault.rglob("*"):
        if other.is_file() and other.suffix != ".md":
            rel = other.relative_to(vault).as_posix()
            targets.setdefault(other.name, rel)
            targets[rel] = rel
    return targets


# --- check 1: call graph ---------------------------------------------------------------


def _app_function_names(root: Path) -> set[str]:
    """Bare names of every function defined anywhere in app/ (for the private-leaf rule)."""
    names: set[str] = set()
    app = root / "app"
    for path in sorted(app.rglob("*.py")) if app.is_dir() else []:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names |= {
            n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
    return names


def _called_names(node: ast.AST) -> set[str]:
    called: set[str] = set()
    for call in (n for n in ast.walk(node) if isinstance(n, ast.Call)):
        if isinstance(call.func, ast.Name):
            called.add(call.func.id)
        elif isinstance(call.func, ast.Attribute):
            called.add(call.func.attr)
    return called


def _code_functions(
    path: Path, rel: str, app_functions: frozenset[str] = frozenset()
) -> tuple[set[str], set[str]]:
    """(all function names, names that must have a call-graph row) defined in one file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    defined: set[str] = set()
    required: set[str] = set()
    exempt_file = rel.startswith(EXEMPT_CODE_DIRS)

    def visit(node: ast.FunctionDef | ast.AsyncFunctionDef, owner: str | None) -> None:
        name = f"{owner}.{node.name}" if owner else node.name
        defined.add(name)
        decorators = {
            d.func.id
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
            else d.id
            if isinstance(d, ast.Name)
            else ""
            for d in node.decorator_list
        }
        is_dunder = node.name.startswith("__") and node.name.endswith("__")
        is_private_leaf = (
            node.name.startswith("_")
            and not is_dunder
            and not (_called_names(node) - {node.name}) & app_functions
        )
        if not (exempt_file or is_dunder or is_private_leaf or decorators & VALIDATOR_DECORATORS):
            required.add(name)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit(node, None)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    visit(item, node.name)
    return defined, required


def check_call_graph(root: Path) -> list[str]:
    flow = root / "docs" / "flow.md"
    if not flow.is_file():
        return ["docs/flow.md not found"]
    text = flow.read_text(encoding="utf-8")
    heading = re.search(r"^## .*Call graph index.*$", text, re.M)
    if heading is None:
        return ["docs/flow.md has no 'Call graph index' section"]
    problems: list[str] = []
    documented: dict[str, set[str]] = defaultdict(set)
    rows = 0
    for line in text[heading.end() :].splitlines():
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set("".join(cells)) <= {"-", ":", " "} or cells[1:2] == ["Function"]:
            continue  # separator or header row
        if len(cells) != 4:
            problems.append(f"call graph row does not have 4 columns: {line.strip()!r}")
            continue
        rows += 1
        function_cell, file_cell = cells[1], cells[3]
        for ref in (part.strip() for part in function_cell.split(" / ")):
            match = FUNCTION_REF.match(ref)
            if match is None:
                problems.append(f"row {function_cell!r}: {ref!r} is not a function reference")
                continue
            documented[file_cell].add(match.group(1))
    if rows == 0:
        problems.append("call graph index has no rows")

    defined_by_file: dict[str, set[str]] = {}
    for rel in sorted(documented):
        path = root / rel
        if not path.is_file():
            problems.append(f"{rel}: file named in the call graph does not exist")
            continue
        defined_by_file[rel] = _code_functions(path, rel)[0]
        for name in sorted(documented[rel] - defined_by_file[rel]):
            problems.append(f"{rel}: {name}() is in the call graph but not defined there")

    app = root / "app"
    app_functions = frozenset(_app_function_names(root))
    for path in sorted(app.rglob("*.py")) if app.is_dir() else []:
        rel = path.relative_to(root).as_posix()
        _, required = _code_functions(path, rel, app_functions)
        for name in sorted(required - documented.get(rel, set())):
            problems.append(f"{rel}: {name}() has no row in the call graph index")
    return problems


# --- checks 2-7: vault ----------------------------------------------------------------


def check_wikilinks(notes: list[Note], vault: Path) -> list[str]:
    targets = _resolver(notes, vault)
    return [
        f"{note.rel}: [[{link}]] does not resolve to a note"
        for note in notes
        for link in note.links
        if link not in targets
    ]


def check_adr_numbers(vault: Path) -> list[str]:
    decisions = vault / "04 Decisions"
    if not decisions.is_dir():
        return ["04 Decisions/ not found"]
    problems: list[str] = []
    numbers: list[int] = []
    for path in sorted(decisions.glob("*.md")):
        match = ADR_FILE.match(path.name)
        if match is None:
            problems.append(f"04 Decisions/{path.name}: name does not match 'ADR-NNN <title>.md'")
        else:
            numbers.append(int(match.group(1)))
    for number, count in sorted(Counter(numbers).items()):
        if count > 1:
            problems.append(f"ADR-{number:03d} is used by {count} notes")
    if numbers:
        for gap in sorted(set(range(1, max(numbers) + 1)) - set(numbers)):
            problems.append(f"ADR-{gap:03d} is missing (numbers must have no gaps)")
    return problems


def check_open_questions(vault: Path) -> list[str]:
    path = vault / "07 Progress" / "Open Questions.md"
    if not path.is_file():
        return ["07 Progress/Open Questions.md not found"]
    text = FENCED_CODE.sub("", path.read_text(encoding="utf-8"))
    problems = [
        f"numbered list item {m.group(0).strip()!r}: write questions as '- **Q<n>.** ...'"
        for m in NUMBERED_ITEM.finditer(text)
    ]
    ids = QUESTION_ENTRY.findall(text)
    if not ids:
        problems.append("no '- **Q<n>.**' entries found")
    for qid, count in sorted(Counter(ids).items()):
        if count > 1:
            problems.append(f"Q{qid} appears {count} times")
    return problems


def check_frontmatter(notes: list[Note]) -> list[str]:
    problems: list[str] = []
    for note in notes:
        fm = note.frontmatter
        if note.frontmatter_error:
            problems.append(f"{note.rel}: invalid frontmatter: {note.frontmatter_error}")
            continue
        if fm is None:
            problems.append(f"{note.rel}: no frontmatter")
            continue
        name, description = fm.get("name"), fm.get("description")
        note_type, status = fm.get("type"), fm.get("status")
        if name != note.stem:
            problems.append(f"{note.rel}: name {name!r} does not match the filename {note.stem!r}")
        if not isinstance(description, str) or not description.strip():
            problems.append(f"{note.rel}: description is missing or empty")
        if not isinstance(note_type, str) or note_type not in STATUSES:
            problems.append(f"{note.rel}: type {note_type!r} is not one of {sorted(STATUSES)}")
        elif status not in STATUSES[note_type]:
            allowed = sorted(STATUSES[note_type])
            problems.append(f"{note.rel}: status {status!r} is not valid for {note_type} {allowed}")
    return problems


def check_orphans(notes: list[Note], vault: Path) -> list[str]:
    targets = _resolver(notes, vault)
    inbound: Counter[str] = Counter()
    for note in notes:
        for link in set(note.links):
            target = targets.get(link)
            if target is not None and target != note.rel:
                inbound[target] += 1
    return [
        f"{note.rel}: no other note links to it"
        for note in notes
        if note.stem not in ORPHAN_EXEMPT and inbound[note.rel] == 0
    ]


def _requirements(root: Path) -> dict[str, str | None]:
    """Normalised package name → pinned version (None when not pinned with ==)."""
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    specs = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        specs.extend(group)
    packages: dict[str, str | None] = {}
    for spec in specs:
        requirement = spec.split(";")[0].strip()
        name = re.split(r"[\[\s=<>!~]", requirement, maxsplit=1)[0]
        pin = re.search(r"==\s*([^\s,;]+)", requirement)
        packages[_normalise(name)] = pin.group(1) if pin else None
    return packages


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def check_stack(notes: list[Note], root: Path) -> list[str]:
    problems: list[str] = []
    stack = {_normalise(n.stem): n for n in notes if n.rel.startswith("05 Stack/")}
    for note in stack.values():
        fm = note.frontmatter or {}
        if "version" not in fm:
            problems.append(f"{note.rel}: no version field")
            continue
        version, status = fm["version"], fm.get("status")
        empty = version == [] or (isinstance(version, str) and not version.strip())
        if empty and status != "planned":
            problems.append(
                f"{note.rel}: version is empty but status is {status} (only planned may be empty)"
            )
    if not (root / "pyproject.toml").is_file():
        return [*problems, "pyproject.toml not found"]
    for package, pin in sorted(_requirements(root).items()):
        stack_note = stack.get(package)
        if stack_note is None:
            problems.append(f"pyproject.toml: {package} has no note in 05 Stack/")
            continue
        note_version = (stack_note.frontmatter or {}).get("version")
        if pin and isinstance(note_version, str) and pin not in note_version:
            problems.append(
                f"{stack_note.rel}: version {note_version!r} does not mention the pinned {pin}"
            )
    return problems


# --- runner ---------------------------------------------------------------------------

CHECKS = (
    "1 call graph",
    "2 wikilinks",
    "3 ADR numbers",
    "4 open-question numbers",
    "5 frontmatter",
    "6 orphans",
    "7 stack notes",
)


def run_checks(root: Path) -> dict[str, list[str]]:
    vault = root / "docs" / "vault"
    notes = load_notes(vault) if vault.is_dir() else []
    return dict(
        zip(
            CHECKS,
            (
                check_call_graph(root),
                check_wikilinks(notes, vault),
                check_adr_numbers(vault),
                check_open_questions(vault),
                check_frontmatter(notes),
                check_orphans(notes, vault),
                check_stack(notes, root),
            ),
            strict=True,
        )
    )


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    results = run_checks(root)
    failures = sum(len(problems) for problems in results.values())
    for check, problems in results.items():
        print(f"[{'FAIL' if problems else 'ok'}] {check}")
        for problem in problems:
            print(f"    - {problem}")
    print(f"vault check: {failures} problem(s)" if failures else "vault check: all checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
