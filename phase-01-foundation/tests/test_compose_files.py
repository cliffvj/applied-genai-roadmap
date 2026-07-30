"""Static contract tests for the Docker Compose application stack."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = PROJECT_ROOT / "compose.yaml"


def read_compose_file() -> str:
    """Read the Compose configuration as UTF-8 text."""
    return COMPOSE_FILE.read_text(encoding="utf-8")


def test_compose_declares_application_services() -> None:
    """Compose should declare the API and mock model service."""
    compose = read_compose_file()

    assert "services:" in compose
    assert "  api:" in compose
    assert "  mock-model-service:" in compose


def test_compose_uses_separate_image_targets() -> None:
    """The API and mock service should use isolated Docker targets."""
    compose = read_compose_file()

    assert "target: production" in compose
    assert "target: mock" in compose
    assert "applied-genai-foundation:0.1.0" in compose
    assert "applied-genai-mock-model-service:0.1.0" in compose


def test_compose_waits_for_healthy_model_service() -> None:
    """The API should wait for a healthy model-service dependency."""
    compose = read_compose_file()

    assert "depends_on:" in compose
    assert "condition: service_healthy" in compose


def test_compose_uses_service_dns_for_model_service() -> None:
    """The API should address its dependency by Compose service name."""
    compose = read_compose_file()

    assert "APPLIED_GENAI_MODEL_SERVICE_BASE_URL: http://mock-model-service:8001" in compose


def test_compose_uses_dependency_aware_api_healthcheck() -> None:
    """Compose health should reflect complete application readiness."""
    compose = read_compose_file()

    assert "/health/ready" in compose
    assert "payload.get('status') == 'ready'" in compose


def test_compose_keeps_mock_service_internal() -> None:
    """The mock service should not publish a host port."""
    compose = read_compose_file()

    assert 'expose:\n      - "8001"' in compose
    assert '"8001:8001"' not in compose
    assert '"127.0.0.1:8000:8000"' in compose


def test_compose_declares_shared_bridge_network() -> None:
    """Both services should share a named bridge network."""
    compose = read_compose_file()

    assert compose.count("- model-network") == 2
    assert "model-network:\n    driver: bridge" in compose


def test_compose_avoids_fixed_container_names() -> None:
    """Compose should retain project-scoped container naming."""
    compose = read_compose_file()

    assert "container_name:" not in compose


def test_compose_runs_services_as_explicit_non_root_user() -> None:
    """Both services should explicitly retain the image's non-root UID."""
    compose = read_compose_file()

    assert compose.count('user: "10001:10001"') == 2


def test_compose_uses_read_only_root_filesystems() -> None:
    """Both service root filesystems should be read-only."""
    compose = read_compose_file()

    assert compose.count("read_only: true") == 2
    assert (
        compose.count(
            "/tmp:mode=1777,uid=10001,gid=10001",
        )
        == 2
    )


def test_compose_drops_linux_capabilities() -> None:
    """Services should not retain unnecessary Linux capabilities."""
    compose = read_compose_file()

    assert compose.count("cap_drop:\n      - ALL") == 2
    assert "cap_add:" not in compose
    assert "privileged:" not in compose


def test_compose_prevents_privilege_escalation() -> None:
    """Services should enable the no-new-privileges control."""
    compose = read_compose_file()

    assert (
        compose.count(
            "security_opt:\n      - no-new-privileges:true",
        )
        == 2
    )


def test_compose_enables_init_processes() -> None:
    """Services should use an init process for signal and child handling."""
    compose = read_compose_file()

    assert compose.count("init: true") == 2


def test_compose_defines_resource_limits() -> None:
    """Each service should have bounded CPU, memory, and PID usage."""
    compose = read_compose_file()

    assert "pids_limit: 64" in compose
    assert "pids_limit: 128" in compose
    assert "mem_limit: 256m" in compose
    assert "mem_limit: 512m" in compose
    assert "cpus: 0.5" in compose
    assert "cpus: 1.0" in compose


def test_compose_bounds_local_log_files() -> None:
    """Container JSON logs should use size and rotation limits."""
    compose = read_compose_file()

    assert compose.count("driver: json-file") == 2
    assert compose.count('max-size: "10m"') == 2
    assert compose.count('max-file: "3"') == 2


def test_compose_bounds_model_service_failure_detection() -> None:
    """Compose should detect model-service failures within probe limits."""
    compose = read_compose_file()

    assert 'APPLIED_GENAI_MODEL_SERVICE_TIMEOUT_SECONDS: "1.0"' in compose
    assert 'APPLIED_GENAI_MODEL_SERVICE_RETRY_ATTEMPTS: "2"' in compose
    assert 'APPLIED_GENAI_MODEL_SERVICE_RETRY_MIN_WAIT_SECONDS: "0.1"' in compose
    assert 'APPLIED_GENAI_MODEL_SERVICE_RETRY_MAX_WAIT_SECONDS: "0.25"' in compose
