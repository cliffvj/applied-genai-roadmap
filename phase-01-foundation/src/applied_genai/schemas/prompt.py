"""Validated schemas for Applied GenAI prompt requests."""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator

from applied_genai.schemas.base import ApiSchema

PromptText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=4000,
    ),
]

SystemPromptText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2000,
    ),
]

ModelIdentifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$",
    ),
]

StopSequence = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
    ),
]


class PromptRequest(ApiSchema):
    """Validated request for a future language-model operation."""

    prompt: PromptText = Field(
        description="User instruction or question submitted to the model.",
        examples=["Explain retrieval-augmented generation."],
    )
    model_id: ModelIdentifier = Field(
        default="local/default",
        description="Identifier of the model that should process the request.",
        examples=["qwen2.5:3b"],
    )
    system_prompt: SystemPromptText | None = Field(
        default=None,
        description="Optional instruction defining the model's behavior.",
        examples=["Answer as a concise infrastructure engineer."],
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature used during model generation.",
    )
    max_tokens: int = Field(
        default=512,
        ge=1,
        le=4096,
        description="Maximum number of tokens that may be generated.",
    )
    stop_sequences: list[StopSequence] = Field(
        default_factory=list,
        max_length=8,
        description="Optional sequences that stop model generation.",
    )

    @field_validator("stop_sequences")
    @classmethod
    def validate_unique_stop_sequences(
        cls,
        value: list[str],
    ) -> list[str]:
        """Reject duplicate stop sequences after normalization."""
        if len(value) != len(set(value)):
            raise ValueError("Stop sequences must be unique.")

        return value


class PromptValidationResponse(ApiSchema):
    """Response confirming that a prompt request passed validation."""

    valid: Literal[True] = Field(
        default=True,
        description="Indicates that the request passed validation.",
    )
    request: PromptRequest = Field(
        description="Normalized and validated prompt request.",
    )
