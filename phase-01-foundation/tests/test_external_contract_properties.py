"""Property-based serialization tests for model-service contracts."""

from hypothesis import given
from hypothesis import strategies as st

from applied_genai.schemas.external import (
    ExternalModelGenerationResponse,
)
from applied_genai.schemas.prompt import (
    GenerationFinishReason,
    PromptGenerationResponse,
    TokenUsage,
)

MODEL_IDENTIFIERS = st.from_regex(
    r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,29}",
    fullmatch=True,
)

GENERATED_TEXTS = st.text(
    alphabet=st.characters(
        blacklist_categories=(
            "Cc",
            "Cs",
        ),
    ),
    min_size=1,
    max_size=500,
).filter(
    lambda value: bool(value.strip()),
)


@given(
    model_id=MODEL_IDENTIFIERS,
    generated_text=GENERATED_TEXTS,
    prompt_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
    completion_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
    finish_reason=st.sampled_from(
        tuple(GenerationFinishReason),
    ),
)
def test_external_generation_contract_json_round_trip(
    model_id: str,
    generated_text: str,
    prompt_tokens: int,
    completion_tokens: int,
    finish_reason: GenerationFinishReason,
) -> None:
    """A valid upstream response should survive JSON serialization."""
    response = ExternalModelGenerationResponse(
        model_id=model_id,
        generated_text=generated_text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        finish_reason=finish_reason,
    )

    restored = ExternalModelGenerationResponse.model_validate_json(
        response.model_dump_json(),
    )

    assert restored == response


@given(
    model_id=MODEL_IDENTIFIERS,
    generated_text=GENERATED_TEXTS,
    prompt_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
    completion_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
    finish_reason=st.sampled_from(
        tuple(GenerationFinishReason),
    ),
)
def test_public_generation_contract_json_round_trip(
    model_id: str,
    generated_text: str,
    prompt_tokens: int,
    completion_tokens: int,
    finish_reason: GenerationFinishReason,
) -> None:
    """A valid public response should preserve nested token accounting."""
    response = PromptGenerationResponse(
        model_id=model_id,
        generated_text=generated_text,
        finish_reason=finish_reason,
        usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=(prompt_tokens + completion_tokens),
        ),
    )

    restored = PromptGenerationResponse.model_validate_json(
        response.model_dump_json(),
    )

    assert restored == response
    assert restored.usage.total_tokens == (prompt_tokens + completion_tokens)
