"""Tests for prompt validation API routes."""

import pytest
from fastapi.testclient import TestClient

from applied_genai.main import app

client = TestClient(app)


def test_validate_prompt_returns_normalized_request() -> None:
    """A valid prompt should be returned in normalized form."""
    response = client.post(
        "/api/v1/prompts/validate",
        json={
            "prompt": "  Explain vector embeddings.  ",
            "model_id": "  qwen2.5:3b  ",
            "temperature": 0.2,
            "max_tokens": 256,
            "stop_sequences": ["  END  "],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "request": {
            "prompt": "Explain vector embeddings.",
            "model_id": "qwen2.5:3b",
            "system_prompt": None,
            "temperature": 0.2,
            "max_tokens": 256,
            "stop_sequences": ["END"],
        },
    }


def test_validate_prompt_rejects_blank_prompt() -> None:
    """A whitespace-only prompt should return HTTP 422."""
    response = client.post(
        "/api/v1/prompts/validate",
        json={
            "prompt": "   ",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("temperature", 2.1),
        ("max_tokens", 0),
        (
            "stop_sequences",
            [f"stop-{index}" for index in range(9)],
        ),
    ],
)
def test_validate_prompt_rejects_invalid_constraints(
    field_name: str,
    invalid_value: object,
) -> None:
    """Requests outside the declared constraints should return HTTP 422."""
    payload: dict[str, object] = {
        "prompt": "Validate this request.",
        field_name: invalid_value,
    }

    response = client.post(
        "/api/v1/prompts/validate",
        json=payload,
    )

    assert response.status_code == 422


def test_validate_prompt_rejects_unknown_fields() -> None:
    """Unexpected request fields should return HTTP 422."""
    response = client.post(
        "/api/v1/prompts/validate",
        json={
            "prompt": "Validate extra fields.",
            "unapproved_parameter": "value",
        },
    )

    assert response.status_code == 422


def test_validate_prompt_rejects_duplicate_stop_sequences() -> None:
    """Duplicate normalized stop sequences should return HTTP 422."""
    response = client.post(
        "/api/v1/prompts/validate",
        json={
            "prompt": "Validate duplicate stops.",
            "stop_sequences": ["END", " END "],
        },
    )

    assert response.status_code == 422


def test_prompt_models_are_available_in_openapi() -> None:
    """The prompt request and response contracts should appear in OpenAPI."""
    response = client.get("/openapi.json")

    assert response.status_code == 200

    openapi_schema = response.json()
    schemas = openapi_schema["components"]["schemas"]
    schema_names = set(schemas)

    assert "/api/v1/prompts/validate" in openapi_schema["paths"]
    assert any(name.startswith("PromptRequest") for name in schema_names)
    assert any(name.startswith("PromptValidationResponse") for name in schema_names)
