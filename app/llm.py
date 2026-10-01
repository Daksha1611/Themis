"""LLM client: a free-tier provider cascade through LiteLLM (ADR-021).

Providers, their order and their models are configuration (`LLM_PROVIDER_CASCADE`,
`LLM_MODELS`, `<PROVIDER>_API_KEY`), never code.
"""

import os

# Use the cost map bundled with the pinned LiteLLM version instead of fetching it from the
# network at import time: reproducible costs, and no network call on import.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import logging  # noqa: E402
from typing import Any  # noqa: E402

import litellm  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.observability.tracing import observe, update  # noqa: E402

logger = logging.getLogger(__name__)
litellm.suppress_debug_info = True


class LLMError(Exception):
    """Every provider in the cascade failed. Carries the last provider's HTTP status if any."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class _ProviderFailed(Exception):
    def __init__(self, reason: str, status_code: int | None) -> None:
        super().__init__(reason)
        self.status_code = status_code


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    # LiteLLM's list-price estimate; actual free-tier spend is $0 (ADR-021).
    cost_usd: float


async def complete(
    messages: list[dict[str, str]],
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> LLMResponse:
    """One chat completion from the first provider in the cascade that succeeds."""
    settings = get_settings()
    max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
    temperature = temperature if temperature is not None else settings.llm_temperature
    attempts: list[str] = []
    last_status: int | None = None

    with observe("llm.complete", input={"cascade": settings.llm_provider_cascade}) as span:
        for provider in settings.llm_provider_cascade:
            model = settings.llm_models.get(provider)
            api_key = settings.api_key_for(provider)
            if not model:
                attempts.append(f"{provider}: skipped (no model configured in LLM_MODELS)")
                logger.debug("LLM cascade: skipping %s, no model configured", provider)
                continue
            if not api_key:
                attempts.append(f"{provider}: skipped (no API key)")
                logger.debug("LLM cascade: skipping %s, no API key", provider)
                continue
            try:
                response = await _call(provider, model, api_key, messages, max_tokens, temperature)
            except _ProviderFailed as exc:
                attempts.append(f"{provider}: {exc}")
                last_status = exc.status_code
                logger.debug("LLM cascade: %s failed (%s); falling back", provider, exc)
                continue
            attempts.append(f"{provider}: ok")
            update(
                span, output={"provider": provider, "model": response.model, "attempts": attempts}
            )
            return response

        update(span, output={"provider": None, "attempts": attempts})
        raise LLMError("all LLM providers failed: " + "; ".join(attempts), last_status)


async def _call(
    provider: str,
    model: str,
    api_key: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> LLMResponse:
    """One provider attempt, traced as its own Langfuse generation."""
    litellm_model = f"{provider}/{model}"
    with observe(
        "llm.generate", as_type="generation", input=messages, metadata={"provider": provider}
    ) as generation:
        update(
            generation,
            model=model,
            model_parameters={"temperature": temperature, "max_tokens": max_tokens},
        )
        try:
            raw: Any = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                api_key=api_key,
            )
        except Exception as exc:
            # Any provider error falls through to the next provider: rate limits, bad keys,
            # retired models (404), oversized requests, outages (ADR-021, Free Tier Throughput).
            status = getattr(exc, "status_code", None)
            status = status if isinstance(status, int) else None
            raise _ProviderFailed(f"{type(exc).__name__} (status {status})", status) from exc

        content = raw.choices[0].message.content or ""
        if not content.strip():
            raise _ProviderFailed("empty response", None)
        usage = raw.usage
        result = LLMResponse(
            content=content,
            provider=provider,
            model=raw.model or model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=_cost(raw, provider, model),
        )
        # Reasoning models think before answering; Langfuse's best practices say to capture it.
        # LiteLLM exposes it as `reasoning_content` for most providers but `reasoning` for Groq.
        message = raw.choices[0].message
        reasoning = getattr(message, "reasoning_content", None) or getattr(
            message, "reasoning", None
        )
        details = getattr(usage, "completion_tokens_details", None)
        reasoning_tokens = getattr(details, "reasoning_tokens", None)
        # Output as an OpenAI-format assistant message so Langfuse renders it, with the thinking
        # alongside (metadata values are truncated, so it cannot live there).
        output: dict[str, Any] = {"role": "assistant", "content": content}
        if reasoning:
            output["reasoning_content"] = reasoning
        update(
            generation,
            output=output,
            model=result.model,
            usage_details={"input": result.prompt_tokens, "output": result.completion_tokens},
            cost_details={"total": result.cost_usd},
            # Reasoning tokens are already in "output"; metadata only, to avoid double counting.
            metadata={"provider": provider, "reasoning_tokens": reasoning_tokens},
        )
    return result


def _cost(response: Any, provider: str, model: str) -> float:
    # Provider passed explicitly: model IDs can contain "/" (e.g. Groq's "openai/gpt-oss-120b"),
    # which LiteLLM would otherwise misread as the provider.
    try:
        return float(
            litellm.completion_cost(
                completion_response=response, model=model, custom_llm_provider=provider
            )
        )
    except Exception:
        logger.warning("No LiteLLM cost available for %s/%s; recording 0.0", provider, model)
        return 0.0
