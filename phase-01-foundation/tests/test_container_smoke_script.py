"""Static contract tests for automated container validation."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "container_smoke_test.py"


def read_smoke_script() -> str:
    """Read the container smoke-test script."""
    return SMOKE_SCRIPT.read_text(
        encoding="utf-8",
    )


def test_smoke_script_starts_and_stops_compose_stack() -> None:
    """The workflow should manage its own Compose lifecycle."""
    script = read_smoke_script()

    assert '"up",' in script
    assert '"--wait",' in script
    assert '"down",' in script
    assert '"--remove-orphans",' in script


def test_smoke_script_validates_health_contracts() -> None:
    """The workflow should validate liveness and readiness."""
    script = read_smoke_script()

    assert '"/health/live"' in script
    assert '"/health/ready"' in script
    assert '"not_ready"' in script
    assert '"unavailable"' in script


def test_smoke_script_validates_prompt_generation() -> None:
    """The workflow should test end-to-end model generation."""
    script = read_smoke_script()

    assert '"/api/v1/prompts/generate"' in script
    assert "Explain GPU memory allocation." in script


def test_smoke_script_runs_dependency_recovery_drill() -> None:
    """The workflow should stop and restart the model dependency."""
    script = read_smoke_script()

    assert '"stop",' in script
    assert '"start",' in script
    assert '"mock-model-service",' in script
    assert '"unhealthy"' in script
    assert '"healthy"' in script


def test_smoke_script_checks_runtime_hardening() -> None:
    """The workflow should inspect container security controls."""
    script = read_smoke_script()

    assert "ReadonlyRootfs" in script
    assert "CapDrop" in script
    assert "SecurityOpt" in script
    assert "PidsLimit" in script
    assert "NanoCpus" in script


def test_smoke_script_handles_http_timeouts() -> None:
    """Transient host-side HTTP timeouts should enter the polling loop."""
    script = read_smoke_script()

    assert "HTTP_REQUEST_TIMEOUT_SECONDS" in script
    assert "except TimeoutError as exc:" in script
    assert "timed out after" in script
