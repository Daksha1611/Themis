from unittest.mock import AsyncMock

import litellm
import pytest
from litellm import exceptions as litellm_exceptions

from app import llm
from app.llm import LLMError, complete


def model_response(content: str, prompt: int, completion: int, model: str) -> litellm.ModelResponse:
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


async def test_complete_returns_populated_response(monkeypatch: pytest.MonkeyPatch) -> None:
    acompletion = AsyncMock(return_value=model_response("[]", 100, 20, "openai/gpt-4o-mini"))
    monkeypatch.setattr(llm.litellm, "acompletion", acompletion)

    result = await complete([{"role": "user", "content": "hi"}])

    assert result.content == "[]"
    assert result.model == "openai/gpt-4o-mini"
    assert (result.prompt_tokens, result.completion_tokens, result.total_tokens) == (100, 20, 120)
    assert result.cost_usd == pytest.approx(100 * 1.5e-07 + 20 * 6e-07)
    kwargs = acompletion.await_args.kwargs
    assert kwargs["model"] == "openrouter/openai/gpt-4o-mini"
    assert kwargs["temperature"] == 0.0 and kwargs["max_tokens"] == 2048
    assert kwargs["api_key"] == "sk-or-test"


async def test_model_and_tokens_come_from_the_response(monkeypatch: pytest.MonkeyPatch) -> None:
    response = model_response("ok", 7, 3, "openai/gpt-4o-mini-2024-07-18")
    monkeypatch.setattr(llm.litellm, "acompletion", AsyncMock(return_value=response))

    result = await complete([{"role": "user", "content": "hi"}])

    assert result.model == "openai/gpt-4o-mini-2024-07-18"
    assert (result.prompt_tokens, result.completion_tokens, result.total_tokens) == (7, 3, 10)


async def test_api_error_becomes_llm_error_with_status(monkeypatch: pytest.MonkeyPatch) -> None:
    error = litellm_exceptions.APIError(
        status_code=502, message="bad gateway", llm_provider="openrouter", model="m"
    )
    monkeypatch.setattr(llm.litellm, "acompletion", AsyncMock(side_effect=error))

    with pytest.raises(LLMError) as excinfo:
        await complete([{"role": "user", "content": "hi"}])
    assert excinfo.value.status_code == 502
    assert "bad gateway" in str(excinfo.value)


async def test_other_litellm_errors_are_wrapped_too(monkeypatch: pytest.MonkeyPatch) -> None:
    # RateLimitError is not a subclass of litellm.exceptions.APIError.
    error = litellm_exceptions.RateLimitError(
        message="slow down", llm_provider="openrouter", model="m"
    )
    assert not isinstance(error, litellm_exceptions.APIError)
    monkeypatch.setattr(llm.litellm, "acompletion", AsyncMock(side_effect=error))

    with pytest.raises(LLMError) as excinfo:
        await complete([{"role": "user", "content": "hi"}])
    assert excinfo.value.status_code == 429
