"""Typed data contracts: webhook payloads, review jobs, findings, and review results."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from app.taxonomy import ALLOWED_CATEGORIES, SECURITY_OTHER


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
    base: _Head | None = None


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
    # The base commit: the old side of the diff, where the repo context is taken from (M4).
    # Empty for jobs queued before it existed; the context builder then asks GitHub.
    base_sha: str = ""

    @classmethod
    def from_payload(cls, payload: WebhookPayload) -> Self:
        return cls(
            installation_id=payload.installation.id,
            repo_full_name=payload.repository.full_name,
            pr_number=payload.pull_request.number,
            head_sha=payload.pull_request.head.sha,
            pr_title=payload.pull_request.title,
            base_sha=payload.pull_request.base.sha if payload.pull_request.base else "",
        )


Severity = Literal["critical", "high", "medium", "low"]


class Finding(BaseModel):
    """One review finding. Never free text."""

    file: str
    # A range, not a single line: bug-location matching compares against a labeled range (Q23).
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    # Logic-bug taxonomy (ADR-019), CWE ID (ADR-022), or "security-other". Validated.
    category: str
    subcategory: str | None = None
    severity: Severity
    message: str
    suggestion: str
    # Set by the precision filter, never by the LLM (ADR-016). 0.0 until the filter exists (M5).
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    # What the LLM reported about itself. Stored for analysis; never used for filtering.
    raw_llm_confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"category {self.category!r} is not in the taxonomy")
        if self.category == SECURITY_OTHER and not self.subcategory:
            raise ValueError("category 'security-other' requires a subcategory")
        return self


class RelatedChunk(BaseModel):
    """Code from elsewhere in the repository, retrieved for a diff ([[Context Builder]])."""

    path: str
    symbol: str
    code: str
    score: float
    reason: str
    start_line: int
    end_line: int
    tokens: int
    source: Literal["definition", "caller", "semantic"] = "semantic"
    via: str | None = None  # the referenced or changed name behind a structural chunk
    ambiguous: bool = False


class ReviewContext(BaseModel):
    """What the context builder adds to a review (M4, ADR-027, ADR-028). Empty when off."""

    related_chunks: list[RelatedChunk] = Field(default_factory=list)
    token_budget: int = 0
    token_budget_used: int = 0


class PRRef(BaseModel):
    repo: str
    number: int
    head_sha: str


class LLMConfig(BaseModel):
    # Which cascade provider answered (ADR-021); None when no LLM call succeeded.
    provider: str | None = None
    model: str
    temperature: float
    max_tokens: int


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ReviewResult(BaseModel):
    """The record of one review run."""

    run_id: str
    pr_ref: PRRef
    findings: list[Finding]
    raw_finding_count: int
    # Same as raw until the precision filter exists (M5).
    filtered_finding_count: int
    # `model_config` is reserved by Pydantic v2, hence `llm_config`.
    llm_config: LLMConfig
    token_usage: TokenUsage
    cost_usd: float
    latency_ms: int
    # Always False until guardrails exist.
    guardrail_triggered: bool
    status: Literal["success", "partial", "failed"]
    error: str | None
