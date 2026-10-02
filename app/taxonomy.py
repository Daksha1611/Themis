"""The finding category taxonomy: logic bugs (ADR-019) and security weaknesses (ADR-022)."""

# ADR-019. Category ID → one-line description used in the review prompt.
LOGIC_CATEGORIES: dict[str, str] = {
    "null-or-none-handling": "a value that can be None (or missing) is used without a check",
    "off-by-one-or-boundary": "wrong loop bounds, index, slice, or range edge",
    "error-handling": "exceptions swallowed, raised wrongly, or not handled",
    "concurrency-or-async": "race conditions, missing awaits, unsafe shared state, cancellation",
    "resource-leak": "files, sockets, connections, or locks not released",
    "type-or-contract": "wrong type, wrong return value, or a broken function contract",
    "control-flow": "wrong condition, branch, early return, or loop logic",
    # ADR-023
    "arithmetic-or-numeric": (
        "wrong arithmetic, division by zero, float precision, or overflow of floats, "
        "fixed-width types or size limits"
    ),
}

# ADR-023: how overlapping categories are decided. Shared verbatim by the review prompt, the
# Glossary and the benchmark labelling rules, so labels and model use the same definitions.
PRECEDENCE_RULES: tuple[str, ...] = (
    "Arithmetic operators (+ - * / // % **) used wrongly -> arithmetic-or-numeric. "
    "Comparisons at a range edge (< vs <=) -> off-by-one-or-boundary.",
    "A computation that can divide by zero -> arithmetic-or-numeric. "
    "A ZeroDivisionError that is caught or handled wrongly -> error-handling.",
    "Overflow is scoped to what Python can actually overflow: floats (inf/nan), fixed-width "
    "types (numpy, struct, ctypes), and size limits. Python ints do not overflow.",
    "Float precision errors -> arithmetic-or-numeric.",
)

# ADR-022: the Python-reachable subset of the CWE Top 25 (2024 edition), verified against
# MITRE's CWE view 1430 (CWE 4.20).
SECURITY_CATEGORIES: dict[str, str] = {
    "CWE-20": "improper input validation",
    "CWE-22": "path traversal",
    "CWE-78": "OS command injection",
    "CWE-79": "cross-site scripting in generated HTML",
    "CWE-89": "SQL injection",
    "CWE-94": "code injection (eval, exec, dynamic import of untrusted input)",
    "CWE-200": "exposure of sensitive information",
    "CWE-400": "uncontrolled resource consumption",
    "CWE-502": "deserialization of untrusted data (pickle, unsafe YAML)",
    "CWE-798": "hard-coded credentials",
    "CWE-918": "server-side request forgery",
}

# Any other security issue. Requires a free-text subcategory (Q39).
SECURITY_OTHER = "security-other"

ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {*LOGIC_CATEGORIES, *SECURITY_CATEGORIES, SECURITY_OTHER}
)


def prompt_category_list() -> str:
    """The category list as it appears in the review prompt."""
    lines = ["Logic bugs:"]
    lines += [f"  {cid}: {desc}" for cid, desc in LOGIC_CATEGORIES.items()]
    lines.append("Security issues:")
    lines += [f"  {cid}: {desc}" for cid, desc in SECURITY_CATEGORIES.items()]
    lines.append(
        f'  {SECURITY_OTHER}: any other security issue; also set "subcategory" to a short name'
    )
    lines.append("When two categories could apply:")
    lines += [f"  - {rule}" for rule in PRECEDENCE_RULES]
    return "\n".join(lines)
