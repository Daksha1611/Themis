from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas import Finding
from app.taxonomy import ALLOWED_CATEGORIES, LOGIC_CATEGORIES, SECURITY_CATEGORIES


def finding(**overrides: Any) -> Finding:
    fields: dict[str, Any] = {
        "file": "a.py",
        "line_start": 3,
        "line_end": 4,
        "category": "off-by-one-or-boundary",
        "severity": "high",
        "message": "Loop skips the last element.",
        "suggestion": "Use range(len(xs)).",
        "raw_llm_confidence": 0.7,
    }
    fields.update(overrides)
    return Finding.model_validate(fields)


@pytest.mark.parametrize("category", sorted(ALLOWED_CATEGORIES - {"security-other"}))
def test_every_taxonomy_category_is_accepted(category: str) -> None:
    assert finding(category=category).category == category


@pytest.mark.parametrize(
    "category", ["bug", "logic bug", "A03:2021-Injection", "CWE-327", "cwe-89"]
)
def test_category_outside_the_taxonomy_is_rejected(category: str) -> None:
    with pytest.raises(ValidationError, match="not in the taxonomy"):
        finding(category=category)


def test_security_other_requires_subcategory() -> None:
    with pytest.raises(ValidationError, match="requires a subcategory"):
        finding(category="security-other")
    assert finding(category="security-other", subcategory="weak hash").subcategory == "weak hash"


def test_taxonomy_sizes() -> None:
    assert len(LOGIC_CATEGORIES) == 8  # ADR-019 + ADR-023 (arithmetic-or-numeric)
    assert len(SECURITY_CATEGORIES) == 11  # ADR-022


def test_prompt_carries_the_precedence_rules() -> None:
    from app.taxonomy import PRECEDENCE_RULES, prompt_category_list

    listing = prompt_category_list()
    assert "arithmetic-or-numeric" in listing
    for rule in PRECEDENCE_RULES:
        assert rule in listing
