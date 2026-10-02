import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "check_vault", Path(__file__).resolve().parent.parent / "scripts" / "check_vault.py"
)
assert _SPEC is not None and _SPEC.loader is not None
check_vault: ModuleType = importlib.util.module_from_spec(_SPEC)
sys.modules["check_vault"] = check_vault
_SPEC.loader.exec_module(check_vault)


def note(name: str, note_type: str, status: str, body: str, version: str | None = None) -> str:
    extra = f"version: {version}\n" if version is not None else ""
    return (
        f'---\nname: {name}\ndescription: "The {name} note."\ntype: {note_type}\n'
        f'status: {status}\ntags: [{note_type}]\nrelated:\n  - "[[00 Index]]"\n{extra}---\n\n'
        f"# {name}\n\n{body}\n"
    )


FILES = {
    "pyproject.toml": (
        '[project]\nname = "fixture"\nversion = "0"\n'
        'dependencies = ["httpx==0.28.1", "sqlalchemy[asyncio]==2.1.1"]\n'
        '[project.optional-dependencies]\ndev = ["pytest==9.1.1"]\n'
    ),
    "app/__init__.py": "",
    "app/svc.py": (
        "from pydantic import BaseModel, field_validator\n\n\n"
        "def helper() -> int:\n    return 1\n\n\n"
        "class Model(BaseModel):\n    x: int\n\n"
        "    def __init__(self) -> None:\n        super().__init__(x=helper())\n\n"
        '    @field_validator("x")\n    @classmethod\n'
        "    def _check(cls, value: int) -> int:\n        return value\n\n"
        "    def total(self) -> int:\n        return self.x\n"
    ),
    "app/storage/migrations/versions/0001_init.py": "def upgrade() -> None:\n    pass\n",
    "app/storage/migrations/env.py": "def run_migrations_online() -> None:\n    pass\n",
    "app/leaf.py": (
        "def public() -> int:\n    return _leaf() + _caller()\n\n\n"
        "def _leaf() -> int:\n    return len([1])\n\n\n"
        "def _caller() -> int:\n    return public_helper()\n\n\n"
        "def public_helper() -> int:\n    return 1\n"
    ),
    "docs/flow.md": (
        "# Flow\n\n## 10. Call graph index\n\n"
        "| Caller | Function | Calls | File |\n|---|---|---|---|\n"
        "| main | helper() | — | app/svc.py |\n"
        "| main | Model.total() | — | app/svc.py |\n"
        "| main | public() | _leaf(), _caller() | app/leaf.py |\n"
        "| public() | _caller() | public_helper() | app/leaf.py |\n"
        "| _caller() | public_helper() | — | app/leaf.py |\n"
    ),
    "docs/vault/00 Index.md": note(
        "00 Index",
        "project",
        "in-progress",
        "[[00 Brief]] [[ADR-001 First]] [[ADR-002 Second]] [[httpx]] [[SQLAlchemy]] [[pytest]] "
        "[[Open Questions]] [[Caddy]] [[Map.canvas|Map]] [[08 Results/README|Results]]",
    ),
    "docs/vault/00 Brief.md": note("00 Brief", "project", "in-progress", "Read [[00 Index]]."),
    "docs/vault/Map.canvas": "{}",
    "docs/vault/04 Decisions/ADR-001 First.md": note("ADR-001 First", "decision", "accepted", ""),
    "docs/vault/04 Decisions/ADR-002 Second.md": note(
        "ADR-002 Second", "decision", "superseded", "Replaces [[ADR-001 First]]."
    ),
    "docs/vault/05 Stack/httpx.md": note("httpx", "tech", "done", "", version="0.28.1"),
    "docs/vault/05 Stack/SQLAlchemy.md": note(
        "SQLAlchemy", "tech", "done", "", version='"2.1.1 (asyncio extra)"'
    ),
    "docs/vault/05 Stack/pytest.md": note("pytest", "tech", "done", "", version="9.1.1"),
    "docs/vault/05 Stack/Caddy.md": note("Caddy", "tech", "planned", "", version=""),
    "docs/vault/07 Progress/Open Questions.md": note(
        "Open Questions",
        "progress",
        "in-progress",
        "## Still open\n- **Q2. Two.** Open.\n- **Q2b. Two, part b.** Open.\n\n"
        "## Resolved\n- **Q1.** Done.",
    ),
    "docs/vault/08 Results/README.md": note("README", "reliability", "planned", "Real runs only."),
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for rel, content in FILES.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp_path


def edit(repo: Path, rel: str, old: str, new: str) -> None:
    path = repo / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {rel}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def failing(repo: Path) -> dict[str, list[str]]:
    return {check: problems for check, problems in check_vault.run_checks(repo).items() if problems}


def test_valid_fixture_passes(repo: Path) -> None:
    assert failing(repo) == {}
    assert check_vault.main(["check_vault.py", str(repo)]) == 0


def _missing_function(repo: Path) -> None:
    edit(repo, "docs/flow.md", "| main | helper() |", "| main | renamed() |")


def _undocumented_function(repo: Path) -> None:
    edit(repo, "app/svc.py", "def helper()", "def other() -> None:\n    pass\n\n\ndef helper()")


def _non_function_row(repo: Path) -> None:
    edit(repo, "docs/flow.md", "| main | helper() |", "| main | helper() / startup step |")


def _broken_link(repo: Path) -> None:
    edit(repo, "docs/vault/00 Brief.md", "Read [[00 Index]].", "Read [[00 Index]] and [[Nowhere]].")


def _duplicate_adr(repo: Path) -> None:
    (repo / "docs/vault/04 Decisions/ADR-002 Third.md").write_text(
        note("ADR-002 Third", "decision", "accepted", "[[ADR-001 First]]"), encoding="utf-8"
    )
    edit(repo, "docs/vault/00 Index.md", "[[httpx]]", "[[httpx]] [[ADR-002 Third]]")


def _adr_gap(repo: Path) -> None:
    (repo / "docs/vault/04 Decisions/ADR-002 Second.md").rename(
        repo / "docs/vault/04 Decisions/ADR-003 Second.md"
    )
    edit(repo, "docs/vault/04 Decisions/ADR-003 Second.md", "name: ADR-002", "name: ADR-003")
    edit(repo, "docs/vault/00 Index.md", "[[ADR-002 Second]]", "[[ADR-003 Second]]")


def _duplicate_question(repo: Path) -> None:
    edit(repo, "docs/vault/07 Progress/Open Questions.md", "- **Q1.** Done.", "- **Q2.** Done.")


def _numbered_question(repo: Path) -> None:
    edit(repo, "docs/vault/07 Progress/Open Questions.md", "- **Q1.** Done.", "1. Done.")


def _name_mismatch(repo: Path) -> None:
    edit(repo, "docs/vault/05 Stack/pytest.md", "name: pytest", "name: PyTest")


def _empty_description(repo: Path) -> None:
    edit(repo, "docs/vault/05 Stack/pytest.md", '"The pytest note."', '""')


def _bad_status(repo: Path) -> None:
    edit(repo, "docs/vault/04 Decisions/ADR-001 First.md", "status: accepted", "status: done")


def _bad_type(repo: Path) -> None:
    edit(repo, "docs/vault/00 Brief.md", "type: project", "type: brief")


def _orphan(repo: Path) -> None:
    edit(repo, "docs/vault/00 Index.md", " [[Caddy]]", "")


def _package_without_note(repo: Path) -> None:
    edit(repo, "pyproject.toml", '"httpx==0.28.1"', '"httpx==0.28.1", "uvicorn==0.54.0"')


def _empty_version(repo: Path) -> None:
    edit(repo, "docs/vault/05 Stack/httpx.md", "version: 0.28.1", "version:")


def _stale_version(repo: Path) -> None:
    edit(repo, "pyproject.toml", "httpx==0.28.1", "httpx==0.29.0")


def _empty_version_not_planned(repo: Path) -> None:
    # Caddy's version is empty, which is only allowed while it is planned.
    edit(repo, "docs/vault/05 Stack/Caddy.md", "status: planned", "status: in-progress")


BREAKS: dict[str, tuple[str, Callable[[Path], None]]] = {
    "function missing from code": ("1 call graph", _missing_function),
    "function missing from call graph": ("1 call graph", _undocumented_function),
    "non-function row": ("1 call graph", _non_function_row),
    "broken wikilink": ("2 wikilinks", _broken_link),
    "duplicate ADR number": ("3 ADR numbers", _duplicate_adr),
    "gap in ADR numbers": ("3 ADR numbers", _adr_gap),
    "duplicate question": ("4 open-question numbers", _duplicate_question),
    "question as numbered list": ("4 open-question numbers", _numbered_question),
    "name mismatch": ("5 frontmatter", _name_mismatch),
    "empty description": ("5 frontmatter", _empty_description),
    "status invalid for type": ("5 frontmatter", _bad_status),
    "unknown type": ("5 frontmatter", _bad_type),
    "orphan note": ("6 orphans", _orphan),
    "package without stack note": ("7 stack notes", _package_without_note),
    "empty version": ("7 stack notes", _empty_version),
    "version not the pinned one": ("7 stack notes", _stale_version),
    "empty version but not planned": ("7 stack notes", _empty_version_not_planned),
}


@pytest.mark.parametrize("breakage", list(BREAKS))
def test_each_check_fails_on_broken_fixture(repo: Path, breakage: str) -> None:
    expected_check, apply = BREAKS[breakage]
    apply(repo)
    failures = failing(repo)
    assert list(failures) == [expected_check], failures
    assert check_vault.main(["check_vault.py", str(repo)]) == 1


def test_exempt_functions_need_no_row(repo: Path) -> None:
    # Defined in the fixture without call-graph rows: Model.__init__ (dunder), Model._check
    # (validator), the revision's upgrade() and env.py's run_migrations_online() (migrations
    # dir), and _leaf() (private, calls no app/ function).
    assert "1 call graph" not in failing(repo)


def test_private_helper_that_calls_app_code_needs_a_row(repo: Path) -> None:
    edit(repo, "docs/flow.md", "| public() | _caller() | public_helper() | app/leaf.py |\n", "")
    assert any("_caller() has no row" in p for p in failing(repo).get("1 call graph", []))


def test_empty_version_allowed_while_planned(repo: Path) -> None:
    assert "7 stack notes" not in failing(repo)  # Caddy: planned, empty version


def test_frontmatter_parser_handles_vault_forms() -> None:
    parsed = check_vault.parse_frontmatter(
        '---\nname: X\ndescription: "a: b, \\"c\\""\ntags: [tech, x]\n'
        'related:\n  - "[[A]]"\n  - "[[B]]"\nversion: 1.2.3\n---\nbody\n'
    )
    assert parsed == {
        "name": "X",
        "description": 'a: b, "c"',
        "tags": ["tech", "x"],
        "related": ["[[A]]", "[[B]]"],
        "version": "1.2.3",
    }


def test_frontmatter_parser_rejects_stray_list_item() -> None:
    with pytest.raises(check_vault.FrontmatterError):
        check_vault.parse_frontmatter('---\nversion: 1\n  - "[[A]]"\n---\n')
