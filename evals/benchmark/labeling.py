"""Pure labelling logic for benchmark cases: label spans, cosmetic-change detection, categories.

Category inference applies the same precedence rules the review prompt states
(`app.taxonomy.PRECEDENCE_RULES`, ADR-023), so labels and model use the same definitions.
"""

import ast
import re
from dataclasses import dataclass

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class Span:
    file: str
    line_start: int
    line_end: int


# --- label spans --------------------------------------------------------------------------


def label_spans(diff: str) -> list[Span]:
    """Line spans the change touches, in the new side's line numbers.

    Added lines form contiguous spans. A run of only removed lines (nothing added in its place)
    is labeled at the deletion point: the new-side lines just before and after it.
    """
    spans: list[Span] = []
    path: str | None = None
    new_line = 0
    run_start: int | None = None
    pending_deletion = False

    def close_run(end: int) -> None:
        nonlocal run_start
        if path is not None and run_start is not None:
            spans.append(Span(path, run_start, end))
        run_start = None

    def flush_deletion() -> None:
        nonlocal pending_deletion
        if pending_deletion and path is not None:
            spans.append(Span(path, max(1, new_line - 1), max(1, new_line)))
        pending_deletion = False

    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            close_run(new_line - 1)
            flush_deletion()
            target = raw[4:]
            path = target[2:] if target.startswith("b/") else None
            continue
        if raw.startswith(("diff --git", "--- ", "index ", "new file", "deleted file")):
            continue
        header = HUNK_HEADER.match(raw)
        if header:
            close_run(new_line - 1)
            flush_deletion()
            new_line = int(header.group(1))
            continue
        if raw.startswith("+"):
            pending_deletion = False  # a replacement, not a pure deletion
            if run_start is None:
                run_start = new_line
            new_line += 1
        elif raw.startswith("-"):
            if run_start is None:
                pending_deletion = True
        elif raw.startswith(" "):
            close_run(new_line - 1)
            flush_deletion()
            new_line += 1
    close_run(new_line - 1)
    flush_deletion()
    return spans


# --- cosmetic changes ---------------------------------------------------------------------

IDENTIFIER_FIELDS = {
    ast.Name: "id",
    ast.arg: "arg",
    ast.FunctionDef: "name",
    ast.AsyncFunctionDef: "name",
    ast.ClassDef: "name",
    ast.Attribute: "attr",
    ast.keyword: "arg",
    ast.alias: "asname",
}


def _strip(tree: ast.Module, annotations: bool) -> ast.Module:
    """Remove docstrings (and optionally annotations) so only behaviour-bearing code remains."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
        if annotations:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node.returns = None
            elif isinstance(node, ast.arg):
                node.annotation = None
            elif isinstance(node, ast.AnnAssign):
                node.annotation = ast.Constant(value=None)
    return tree


def _identifiers(tree: ast.AST) -> list[str]:
    names = []
    for node in ast.walk(tree):
        field_name = IDENTIFIER_FIELDS.get(type(node))
        if field_name:
            names.append(str(getattr(node, field_name)))
            setattr(node, field_name, "_")
    return names


def classify_change(before: str | None, after: str | None) -> str:
    """'behavioural', 'cosmetic' (whitespace, comments, docstrings), 'rename' or 'annotation'.

    A file added, deleted or unparseable on either side counts as behavioural.
    """
    if before is None or after is None:
        return "behavioural"
    try:
        old, new = ast.parse(before), ast.parse(after)
    except SyntaxError:
        return "behavioural"
    if ast.dump(_strip(old, False)) == ast.dump(_strip(new, False)):
        return "cosmetic"
    old, new = _strip(old, True), _strip(new, True)
    if ast.dump(old) == ast.dump(new):
        return "annotation"
    old_ids, new_ids = _identifiers(old), _identifiers(new)
    if ast.dump(old) == ast.dump(new) and len(old_ids) == len(new_ids):
        forward: dict[str, str] = {}
        backward: dict[str, str] = {}
        for a, b in zip(old_ids, new_ids, strict=True):
            if forward.setdefault(a, b) != b or backward.setdefault(b, a) != a:
                return "behavioural"  # not a consistent one-to-one renaming
        return "rename"
    return "behavioural"


# --- categories ---------------------------------------------------------------------------

# (category, message pattern, changed-code pattern). Message hits in the subject weigh 2, in
# the body 1; a changed-code hit weighs 1. Patterns are kept specific: an unclear case should
# stay unlabeled rather than be guessed.
LOGIC_RULES: list[tuple[str, str, str | None]] = [
    (
        "null-or-none-handling",
        r"\bnone\b|\bnull\b|nonetype|keyerror|attributeerror|\bmissing (key|value|attribute)",
        r"\bis (not )?None\b|\bor None\b|\.get\(",
    ),
    (
        "off-by-one-or-boundary",
        r"off[- ]by[- ]one|boundary|indexerror|out of (range|bounds)|\bslic(e|ing)\b"
        r"|\bempty (string|list|input|value)|\btruncat|edge case",
        None,
    ),
    (
        "error-handling",
        r"\bexceptions?\b|traceback|swallow|\bcatch(es|ing)?\b|re-?rais|\bexcept\b"
        r"|error (handling|message)|(raises?|raised|raising) (the )?wrong",
        r"^\s*(except\b|raise\b)",
    ),
    (
        "concurrency-or-async",
        r"\basync\b|\bawait|cancel|\bthreads?\b|threading|\brace\b|deadlock|\blocks?\b"
        r"|task ?groups?|event loop|\btrio\b|asyncio|concurren|coroutine",
        r"\bawait\b|\basync (def|with|for)\b|\bcancel|threading\.",
    ),
    (
        "resource-leak",
        r"\bleak|not (being )?closed|unclosed|\bclean ?up\b|file descriptor|resourcewarning"
        r"|dangling",
        r"\.a?close\(\)",
    ),
    (
        "type-or-contract",
        r"\btypes?\b|\btyping\b|signature|return (value|type)|coerc|\bconvert|serializ"
        r"|\bschema\b|validat",
        None,
    ),
    (
        "control-flow",
        r"\bcondition|\bbranch|early return|\bloop\b|not (being )?(applied|respected|honou?red"
        r"|called|triggered|used)|\bignor(ed|es|ing)\b|precedence|\bwrong order\b",
        None,
    ),
    (
        "arithmetic-or-numeric",
        r"divi(de|sion) by zero|zero ?division|zerodivision|\bfloat|precision|\brounding\b"
        r"|overflow|\bnan\b|\binfinit|arithmetic|numeric",
        r"ZeroDivisionError|\bmath\.|\bround\(|\bfloat\(",
    ),
]

# Security needs an explicit security signal plus a specific weakness; otherwise unlabeled.
SECURITY_SIGNAL = re.compile(
    r"secur|vulnerab|\bcve-|inject|travers|\bxss\b|cross[- ]site|\bssrf\b|denial of service"
    r"|\bdos\b|redos|unsafe (deserial|load|yaml|pickle)",
    re.IGNORECASE,
)
CWE_RULES: list[tuple[str, str]] = [
    ("CWE-89", r"sql injection"),
    ("CWE-22", r"path traversal|directory traversal|\btravers"),
    ("CWE-78", r"command injection|shell injection|shell=true"),
    ("CWE-79", r"\bxss\b|cross[- ]site scripting|html injection"),
    ("CWE-94", r"code injection|\beval\b|\bexec\b"),
    ("CWE-502", r"deserializ|\bpickle\b|unsafe (yaml|load)"),
    ("CWE-918", r"\bssrf\b|server[- ]side request"),
    ("CWE-798", r"hard-?coded (credential|password|secret|token)"),
    ("CWE-200", r"(leak|expos)\w* (of )?(sensitive|secret|credential|password|token)"),
    ("CWE-400", r"denial of service|\bdos\b|redos|resource exhaustion|unbounded"),
    ("CWE-20", r"input validation|unvalidated input|untrusted input"),
]


@dataclass(frozen=True)
class Category:
    label: str | None
    reason: str


def changed_code(diff: str) -> list[str]:
    return [
        line[1:]
        for line in diff.splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]


def infer_category(subject: str, message: str, diff: str) -> Category:
    """Infer the case's category from the fix's message and code; None when unclear."""
    text = f"{subject}\n{message}"
    body = message[len(subject) :] if message.startswith(subject) else message
    code = "\n".join(changed_code(diff))

    if SECURITY_SIGNAL.search(text):
        for cwe, pattern in CWE_RULES:
            if re.search(pattern, text, re.IGNORECASE):
                return Category(cwe, f"security signal and '{pattern}' in message")
        return Category(None, "security signal but no specific weakness")

    # Precedence (ADR-023): a ZeroDivisionError that is caught or handled -> error-handling;
    # a computation that can divide by zero -> arithmetic-or-numeric.
    if re.search(r"^\s*except\b.*ZeroDivisionError", code, re.M):
        return Category("error-handling", "ZeroDivisionError handling changed")

    scores: dict[str, int] = {}
    for category, message_pattern, code_pattern in LOGIC_RULES:
        score = 2 * bool(re.search(message_pattern, subject, re.IGNORECASE))
        score += bool(re.search(message_pattern, body, re.IGNORECASE))
        if code_pattern:
            score += bool(re.search(code_pattern, code, re.M))
        if score:
            scores[category] = score
    if not scores:
        return Category(None, "no category signal")
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    top, top_score = ranked[0]
    if top_score < 2:
        return Category(None, f"weak signal only ({top}={top_score})")
    if len(ranked) > 1 and ranked[1][1] == top_score:
        return Category(None, f"tie: {top}={top_score}, {ranked[1][0]}={ranked[1][1]}")
    return Category(top, f"scores {dict(ranked)}")
