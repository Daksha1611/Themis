from collections.abc import Callable
from typing import Any

import litellm
import pytest
from litellm import exceptions as litellm_exceptions
from pydantic import SecretStr

from app import llm
from app.config import get_settings
from app.llm import LLMError, complete

MESSAGES = [{"role": "user", "content": "review this"}]


def model_response(content: str, model: str, prompt: int = 100, completion: int = 20) -> Any:
    return litellm.ModelResponse(
        model=model,
        choices=[
            litellm.Choices(
                message=litellm.Message(content=content, role="assistant"),
                index=0,
                finish_reason="stop",
            )
        ],
        usage=litellm.Usage(
            prompt_tokens=prompt, completion_tokens=completion, total_tokens=prompt + completion
        ),
    )


def rate_limited(provider: str) -> Exception:
    return litellm_exceptions.RateLimitError(message="slow down", llm_provider=provider, model="m")


class FakeLiteLLM:
    """Stands in for litellm.acompletion: per-provider outcomes, records every call."""

    def __init__(self, outcomes: dict[str, Exception | str]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        provider = kwargs["model"].split("/", 1)[0]
        outcome = self.outcomes[provider]
        if isinstance(outcome, Exception):
            raise outcome
        return model_response(outcome, kwargs["model"].split("/", 1)[1])

    @property
    def providers_called(self) -> list[str]:
        return [c["model"].split("/", 1)[0] for c in self.calls]


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, Exception | str]], FakeLiteLLM]:
    def install(outcomes: dict[str, Exception | str]) -> FakeLiteLLM:
        f = FakeLiteLLM(outcomes)
        monkeypatch.setattr(llm.litellm, "acompletion", f)
        return f

    return install


def use_settings(monkeypatch: pytest.MonkeyPatch, **overrides: Any) -> None:
    settings = get_settings().model_copy(update=overrides)
    monkeypatch.setattr(llm, "get_settings", lambda: settings)


async def test_groq_succeeds(fake: Callable[..., FakeLiteLLM]) -> None:
    f = fake({"groq": "[]"})
    result = await complete(MESSAGES)

    assert result.provider == "groq"
    assert result.model == "openai/gpt-oss-120b"
    assert (result.prompt_tokens, result.completion_tokens, result.total_tokens) == (100, 20, 120)
    assert result.cost_usd == pytest.approx(100 * 1.5e-07 + 20 * 6e-07)  # list-price estimate
    call = f.calls[0]
    assert call["model"] == "groq/openai/gpt-oss-120b" and call["api_key"] == "gsk-test"
    assert call["temperature"] == 0.0 and call["max_tokens"] == 2048


async def test_groq_rate_limited_falls_back_to_gemini(fake: Callable[..., FakeLiteLLM]) -> None:
    f = fake({"groq": rate_limited("groq"), "gemini": "[]"})
    result = await complete(MESSAGES)
    assert result.provider == "gemini" and result.model == "gemini-3.5-flash"
    assert f.providers_called == ["groq", "gemini"]
    assert f.calls[1]["api_key"] == "gm-test"


async def test_two_rate_limited_falls_back_to_mistral(fake: Callable[..., FakeLiteLLM]) -> None:
    f = fake({"groq": rate_limited("groq"), "gemini": rate_limited("gemini"), "mistral": "[]"})
    result = await complete(MESSAGES)
    assert result.provider == "mistral" and result.model == "codestral-2508"
    assert f.providers_called == ["groq", "gemini", "mistral"]


async def test_three_rate_limited_falls_back_to_openrouter(
    fake: Callable[..., FakeLiteLLM],
) -> None:
    f = fake(
        {
            "groq": rate_limited("groq"),
            "gemini": rate_limited("gemini"),
            "mistral": rate_limited("mistral"),
            "openrouter": "[]",
        }
    )
    result = await complete(MESSAGES)
    assert result.provider == "openrouter" and result.model == "qwen/qwen3.8-27b:free"
    assert result.cost_usd == 0.0  # :free model
    assert f.providers_called == ["groq", "gemini", "mistral", "openrouter"]


async def test_all_four_fail_names_every_failure(fake: Callable[..., FakeLiteLLM]) -> None:
    fake(
        {
            "groq": rate_limited("groq"),
            "gemini": litellm_exceptions.AuthenticationError(
                message="bad key", llm_provider="gemini", model="m"
            ),
            "mistral": rate_limited("mistral"),
            "openrouter": litellm_exceptions.NotFoundError(
                message="no such model", llm_provider="openrouter", model="m"
            ),
        }
    )
    with pytest.raises(LLMError) as excinfo:
        await complete(MESSAGES)
    message = str(excinfo.value)
    assert "groq: RateLimitError (status 429)" in message
    assert "gemini: AuthenticationError (status 401)" in message
    assert "mistral: RateLimitError (status 429)" in message
    assert "openrouter: NotFoundError (status 404)" in message
    assert excinfo.value.status_code == 404


async def test_empty_key_is_skipped_without_a_call(
    fake: Callable[..., FakeLiteLLM], monkeypatch: pytest.MonkeyPatch
) -> None:
    use_settings(monkeypatch, groq_api_key=SecretStr(""))
    f = fake({"groq": "[]", "gemini": "[]"})
    result = await complete(MESSAGES)
    assert result.provider == "gemini"
    assert f.providers_called == ["gemini"]  # groq never attempted


async def test_cascade_order_comes_from_config(
    fake: Callable[..., FakeLiteLLM], monkeypatch: pytest.MonkeyPatch
) -> None:
    use_settings(monkeypatch, llm_provider_cascade=["mistral", "groq"])
    f = fake({"mistral": rate_limited("mistral"), "groq": "[]"})
    result = await complete(MESSAGES)
    assert result.provider == "groq"
    assert f.providers_called == ["mistral", "groq"]  # gemini and openrouter not in the list


async def test_retired_model_falls_through(fake: Callable[..., FakeLiteLLM]) -> None:
    # A model can vanish entirely (gemini-2.5-flash returned 404 during model selection).
    f = fake(
        {
            "groq": litellm_exceptions.NotFoundError(
                message="gone", llm_provider="groq", model="m"
            ),
            "gemini": "[]",
        }
    )
    assert (await complete(MESSAGES)).provider == "gemini"
    assert f.providers_called == ["groq", "gemini"]


async def test_empty_content_falls_through(fake: Callable[..., FakeLiteLLM]) -> None:
    fake({"groq": "   ", "gemini": "[]"})
    assert (await complete(MESSAGES)).provider == "gemini"


async def test_api_error_is_wrapped(fake: Callable[..., FakeLiteLLM]) -> None:
    error = litellm_exceptions.APIError(
        status_code=502, message="bad gateway", llm_provider="openrouter", model="m"
    )
    fake({"groq": error, "gemini": error, "mistral": error, "openrouter": error})
    with pytest.raises(LLMError) as excinfo:
        await complete(MESSAGES)
    assert excinfo.value.status_code == 502


def test_unknown_provider_key_comes_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRAS_API_KEY", "cb-test")
    assert get_settings().api_key_for("cerebras") == "cb-test"
    assert get_settings().api_key_for("groq") == "gsk-test"
