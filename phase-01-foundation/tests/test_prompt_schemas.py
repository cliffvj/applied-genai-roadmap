"""Tests for validated GenAI prompt schemas."""

import pytest
from pydantic import ValidationError

from applied_genai.schemas.prompt import (
    GenerationFinishReason,
    PromptGenerationResponse,
    PromptRequest,
    TokenUsage,
)


def test_prompt_request_defaults() -> None:
    """A minimal prompt should receive safe generation defaults."""
    request = PromptRequest(
        prompt="Explain vector embeddings.",
    )

    assert request.prompt == "Explain vector embeddings."
    assert request.model_id == "local/default"
    assert request.system_prompt is None
    assert request.temperature == 0.2
    assert request.max_tokens == 512
    assert request.stop_sequences == []


def test_prompt_request_normalizes_strings() -> None:
    """String values should be stripped before application use."""
    request = PromptRequest(
        prompt="  Explain retrieval-augmented generation.  ",
        model_id="  qwen2.5:3b  ",
        system_prompt="  Respond as an infrastructure engineer.  ",
        stop_sequences=["  END  ", "  STOP  "],
    )

    assert request.prompt == "Explain retrieval-augmented generation."
    assert request.model_id == "qwen2.5:3b"
    assert request.system_prompt == "Respond as an infrastructure engineer."
    assert request.stop_sequences == ["END", "STOP"]


def test_prompt_request_rejects_blank_prompt() -> None:
    """A whitespace-only prompt should be rejected."""
    with pytest.raises(ValidationError):
        PromptRequest.model_validate(
            {
                "prompt": "   ",
            },
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("temperature", -0.01),
        ("temperature", 2.01),
        ("max_tokens", 0),
        ("max_tokens", 4097),
    ],
)
def test_prompt_request_rejects_invalid_numeric_constraints(
    field_name: str,
    invalid_value: object,
) -> None:
    """Generation controls outside supported ranges should be rejected."""
    payload: dict[str, object] = {
        "prompt": "Test the validation rules.",
        field_name: invalid_value,
    }

    with pytest.raises(ValidationError):
        PromptRequest.model_validate(payload)


def test_prompt_request_rejects_duplicate_stop_sequences() -> None:
    """Duplicate stop sequences should fail after whitespace normalization."""
    with pytest.raises(ValidationError):
        PromptRequest.model_validate(
            {
                "prompt": "Test duplicate stops.",
                "stop_sequences": ["END", " END "],
            },
        )


def test_prompt_request_rejects_too_many_stop_sequences() -> None:
    """No more than eight stop sequences should be accepted."""
    with pytest.raises(ValidationError):
        PromptRequest.model_validate(
            {
                "prompt": "Test stop-sequence limits.",
                "stop_sequences": [f"stop-{index}" for index in range(9)],
            },
        )


def test_prompt_request_rejects_unknown_fields() -> None:
    """Prompt contracts should reject undeclared request fields."""
    with pytest.raises(ValidationError):
        PromptRequest.model_validate(
            {
                "prompt": "Test extra field handling.",
                "unsupported_parameter": True,
            },
        )


def test_token_usage_serialization() -> None:
    """Token usage should serialize with a consistent total."""
    usage = TokenUsage(
        prompt_tokens=10,
        completion_tokens=15,
        total_tokens=25,
    )

    assert usage.model_dump() == {
        "prompt_tokens": 10,
        "completion_tokens": 15,
        "total_tokens": 25,
    }


def test_token_usage_rejects_incorrect_total() -> None:
    """A total inconsistent with its components should be rejected."""
    with pytest.raises(ValidationError):
        TokenUsage(
            prompt_tokens=10,
            completion_tokens=15,
            total_tokens=30,
        )


def test_prompt_generation_response_serialization() -> None:
    """A generated response should serialize to the public contract."""
    response = PromptGenerationResponse(
        model_id="qwen2.5:3b",
        generated_text="Generated response.",
        finish_reason=GenerationFinishReason.STOP,
        usage=TokenUsage(
            prompt_tokens=4,
            completion_tokens=3,
            total_tokens=7,
        ),
    )

    assert response.model_dump(mode="json") == {
        "model_id": "qwen2.5:3b",
        "generated_text": "Generated response.",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 4,
            "completion_tokens": 3,
            "total_tokens": 7,
        },
    }
