"""Typed data contracts: webhook payloads, review jobs, findings, and review results."""

from enum import StrEnum
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class _Repository(BaseModel):
    full_name: str


class _Installation(BaseModel):
    id: int


class _Head(BaseModel):
    sha: str


class _PullRequest(BaseModel):
    number: int
    title: str
    head: _Head


class WebhookPayload(BaseModel):
    """The subset of a GitHub `pull_request` webhook payload that Themis reads."""

    action: str
    pull_request: _PullRequest
    repository: _Repository
    installation: _Installation


class ReviewJob(BaseModel):
    """One queued review of one PR head commit."""

    installation_id: int
    repo_full_name: str
    pr_number: int
    head_sha: str
    pr_title: str

    @classmethod
    def from_payload(cls, payload: WebhookPayload) -> Self:
        return cls(
            installation_id=payload.installation.id,
            repo_full_name=payload.repository.full_name,
            pr_number=payload.pull_request.number,
            head_sha=payload.pull_request.head.sha,
            pr_title=payload.pull_request.title,
        )


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Finding(BaseModel):
    """One review finding. Never free text."""

    file: str
    line: int
    # Plain string until Q37b settles the security taxonomy (ADR-009, ADR-019).
    category: str
    subcategory: str | None = None
    severity: Severity
    message: str
    # Set by the precision filter, never by the LLM (ADR-016).
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _security_other_needs_subcategory(self) -> Self:
        if self.category == "security-other" and not self.subcategory:
            raise ValueError("category 'security-other' requires a subcategory")
        return self


class PRRef(BaseModel):
    repo: str
    number: int
    head_sha: str


class ReviewStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ReviewResult(BaseModel):
    """The record of one review run."""

    run_id: UUID
    pr_ref: PRRef
    findings: list[Finding] = Field(default_factory=list)
    raw_finding_count: int
    filtered_finding_count: int
    # `model_config` is reserved by Pydantic v2, hence `llm_config`.
    llm_config: dict[str, Any]
    token_usage: dict[str, int]
    cost_usd: float
    latency_ms: int
    guardrail_triggered: bool
    status: ReviewStatus
    error: str | None = None
