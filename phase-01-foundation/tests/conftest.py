"""Shared pytest configuration, classification, and fixtures."""

from collections.abc import Callable

import pytest

from applied_genai.core.config import Settings
from applied_genai.schemas.external import (
    ExternalModelGenerationResponse,
    ExternalServiceHealthResponse,
)
from applied_genai.schemas.prompt import PromptRequest
from tests.factories import (
    create_generation_response,
    create_health_response,
    create_prompt_payload,
    create_prompt_request,
    create_test_settings,
)

SettingsFactory = Callable[..., Settings]
PromptRequestFactory = Callable[..., PromptRequest]

XDIST_AUTO_WORKERS = 2

TEST_MODULE_MARKERS: dict[str, tuple[str, ...]] = {
    "test_compose_files.py": (
        "unit",
        "contract",
    ),
    "test_config.py": ("unit",),
    "test_container_files.py": (
        "unit",
        "contract",
    ),
    "test_container_smoke_script.py": (
        "unit",
        "contract",
    ),
    "test_external_contract_properties.py": (
        "unit",
        "contract",
        "property",
    ),
    "test_external_schemas.py": ("unit", "contract"),
    "test_main.py": ("integration",),
    "test_model_service_client.py": ("unit", "contract"),
    "test_model_service_generation.py": ("unit", "contract"),
    "test_model_service_lifespan.py": ("integration",),
    "test_model_service_routes.py": ("integration", "contract"),
    "test_package.py": ("unit",),
    "test_prompt_generation_routes.py": (
        "integration",
        "contract",
    ),
    "test_prompt_properties.py": (
        "unit",
        "contract",
        "property",
    ),
    "test_prompt_routes.py": ("integration", "contract"),
    "test_prompt_schemas.py": ("unit", "contract"),
    "test_readiness_routes.py": ("integration", "contract"),
    "test_settings_integration.py": ("integration",),
    "test_settings_properties.py": ("unit", "property"),
    "test_system_routes.py": ("integration", "contract"),
    "test_system_schemas.py": ("unit", "contract"),
}


def pytest_xdist_auto_num_workers(
    config: pytest.Config,
) -> int:
    """Use a stable worker count whenever xdist receives -n auto."""
    del config

    return XDIST_AUTO_WORKERS


def pytest_collection_modifyitems(
    items: list[pytest.Item],
) -> None:
    """Apply central classifications and reject unknown test modules."""
    unclassified_modules: set[str] = set()

    for item in items:
        module_name = item.path.name
        marker_names = TEST_MODULE_MARKERS.get(module_name)

        if marker_names is None:
            unclassified_modules.add(module_name)
            continue

        for marker_name in marker_names:
            item.add_marker(
                getattr(pytest.mark, marker_name),
            )

    if unclassified_modules:
        formatted_modules = "\n".join(
            f"- {module_name}" for module_name in sorted(unclassified_modules)
        )

        raise pytest.UsageError(
            "The following test modules have no classification in "
            "TEST_MODULE_MARKERS:\n"
            f"{formatted_modules}",
        )


@pytest.fixture
def settings_factory() -> SettingsFactory:
    """Return the deterministic application-settings factory."""
    return create_test_settings


@pytest.fixture
def prompt_request_factory() -> PromptRequestFactory:
    """Return the validated prompt-request factory."""
    return create_prompt_request


@pytest.fixture
def test_settings() -> Settings:
    """Return deterministic default test settings."""
    return create_test_settings()


@pytest.fixture
def valid_prompt_payload() -> dict[str, object]:
    """Return a new valid prompt payload for each test."""
    return create_prompt_payload()


@pytest.fixture
def valid_prompt_request() -> PromptRequest:
    """Return a validated prompt request."""
    return create_prompt_request()


@pytest.fixture
def healthy_external_response() -> ExternalServiceHealthResponse:
    """Return a validated healthy upstream response."""
    return create_health_response()


@pytest.fixture
def generated_external_response() -> ExternalModelGenerationResponse:
    """Return a validated upstream generation response."""
    return create_generation_response()
