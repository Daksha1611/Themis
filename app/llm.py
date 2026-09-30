"""LLM client: LiteLLM routed through OpenRouter (ADR-005). The model is configuration, not code."""

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
    """Any failure calling the LLM. Carries the provider's HTTP status code when there is one."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LLMResponse(BaseModel):
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


async def complete(
    messages: list[dict[str, str]],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> LLMResponse:
    """One chat completion. Traced as a Langfuse `generation` under the current observation."""
    settings = get_settings()
    model = model or settings.llm_model
    max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
    temperature = temperature if temperature is not None else settings.llm_temperature
    litellm_model = f"openrouter/{model}"

    with observe("llm.complete", as_type="generation", input=messages) as generation:
        update(
            generation,
            model=model,
            model_parameters={"temperature": temperature, "max_tokens": max_tokens},
        )
        try:
            response: Any = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                api_key=settings.openrouter_api_key.get_secret_value(),
            )
        except Exception as exc:
            # LiteLLM's specific errors (auth, rate limit, timeout, ...) are not subclasses of
            # litellm.exceptions.APIError, so everything is caught and wrapped here.
            status_code = getattr(exc, "status_code", None)
            logger.warning("LLM call to %s failed (status %s): %s", model, status_code, exc)
            raise LLMError(str(exc), status_code if isinstance(status_code, int) else None) from exc

        content = response.choices[0].message.content or ""
        usage = response.usage
        result = LLMResponse(
            content=content,
            model=response.model or model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=_cost(response, litellm_model),
        )
        update(
            generation,
            output=content,
            model=result.model,
            usage_details={"input": result.prompt_tokens, "output": result.completion_tokens},
            cost_details={"total": result.cost_usd},
        )
    return result


def _cost(response: Any, litellm_model: str) -> float:
    try:
        return float(litellm.completion_cost(completion_response=response, model=litellm_model))
    except Exception:
        logger.warning("No LiteLLM cost available for %s; recording 0.0", litellm_model)
        return 0.0
