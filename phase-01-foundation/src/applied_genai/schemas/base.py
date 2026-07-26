"""Shared Pydantic configuration for API schemas."""

from pydantic import BaseModel, ConfigDict


class ApiSchema(BaseModel):
    """Base class for validated API request and response schemas."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
