"""Property-based tests for prompt and token-usage contracts."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from applied_genai.schemas.prompt import (
    PromptRequest,
    TokenUsage,
)

WORD_CHARACTERS = st.characters(
    whitelist_categories=(
        "Ll",
        "Lu",
        "Nd",
    ),
)

WORDS = st.text(
    alphabet=WORD_CHARACTERS,
    min_size=1,
    max_size=20,
)

PROMPT_TEXTS = st.lists(
    WORDS,
    min_size=1,
    max_size=12,
).map(" ".join)

OUTER_WHITESPACE = st.sampled_from(
    (
        "",
        " ",
        "  ",
        "\t",
        "\n",
        " \t ",
    ),
)

STOP_SEQUENCES = st.text(
    alphabet=WORD_CHARACTERS,
    min_size=1,
    max_size=50,
)


@given(
    prompt=PROMPT_TEXTS,
    leading=OUTER_WHITESPACE,
    trailing=OUTER_WHITESPACE,
)
def test_prompt_normalizes_outer_whitespace(
    prompt: str,
    leading: str,
    trailing: str,
) -> None:
    """Valid prompt text should retain content and remove outer whitespace."""
    request = PromptRequest(
        prompt=f"{leading}{prompt}{trailing}",
    )

    assert request.prompt == prompt


@given(
    temperature=st.floats(
        min_value=0.0,
        max_value=2.0,
        allow_nan=False,
        allow_infinity=False,
    ),
    max_tokens=st.integers(
        min_value=1,
        max_value=4096,
    ),
)
def test_prompt_accepts_supported_generation_boundaries(
    temperature: float,
    max_tokens: int,
) -> None:
    """All values inside the declared generation range should validate."""
    request = PromptRequest(
        prompt="Explain Linux GPU scheduling.",
        temperature=temperature,
        max_tokens=max_tokens,
    )

    assert request.temperature == temperature
    assert request.max_tokens == max_tokens


@given(sequence=STOP_SEQUENCES)
def test_prompt_rejects_normalized_duplicate_stop_sequences(
    sequence: str,
) -> None:
    """Stop sequences that normalize to the same value should be rejected."""
    with pytest.raises(
        ValidationError,
        match="Stop sequences must be unique",
    ):
        PromptRequest(
            prompt="Explain GPU memory.",
            stop_sequences=[
                sequence,
                f"  {sequence}  ",
            ],
        )


@given(
    prompt_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
    completion_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
)
def test_token_usage_accepts_consistent_totals(
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """The sum of generated token components should always validate."""
    total_tokens = prompt_tokens + completion_tokens

    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    assert usage.total_tokens == total_tokens


@given(
    prompt_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
    completion_tokens=st.integers(
        min_value=0,
        max_value=1_000_000,
    ),
)
def test_token_usage_rejects_inconsistent_totals(
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """A nonmatching total should always violate the token contract."""
    with pytest.raises(
        ValidationError,
        match="total_tokens must equal",
    ):
        TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=(prompt_tokens + completion_tokens + 1),
        )
