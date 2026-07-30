"""Static contract tests for production container files."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
DOCKERIGNORE = PROJECT_ROOT / ".dockerignore"


def read_project_file(path: Path) -> str:
    """Read one UTF-8 project file."""
    return path.read_text(encoding="utf-8")


def test_dockerfile_uses_pinned_build_images() -> None:
    """The production build should use pinned Python and uv versions."""
    dockerfile = read_project_file(DOCKERFILE)

    assert "ARG PYTHON_IMAGE=python:3.12.13-slim-bookworm" in dockerfile
    assert "ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.12.0" in dockerfile


def test_dockerfile_uses_locked_runtime_dependencies() -> None:
    """The image should install only locked production dependencies."""
    dockerfile = read_project_file(DOCKERFILE)

    assert "uv sync" in dockerfile
    assert "--locked" in dockerfile
    assert "--no-dev" in dockerfile
    assert "--no-install-project" in dockerfile
    assert "--no-editable" in dockerfile


def test_dockerfile_runs_as_non_root() -> None:
    """The runtime process should not execute as root."""
    dockerfile = read_project_file(DOCKERFILE)

    assert "USER 10001:10001" in dockerfile
    assert "--uid 10001" in dockerfile
    assert "--gid 10001" in dockerfile


def test_dockerfile_defines_liveness_healthcheck() -> None:
    """Docker health should use the lightweight liveness endpoint."""
    dockerfile = read_project_file(DOCKERFILE)

    assert "HEALTHCHECK" in dockerfile
    assert "/health/live" in dockerfile
    assert "/health/ready" not in dockerfile


def test_dockerfile_starts_one_uvicorn_process() -> None:
    """The runtime command should start the installed ASGI application."""
    dockerfile = read_project_file(DOCKERFILE)

    assert 'CMD ["python", "-m", "uvicorn", "applied_genai.main:app"]' in dockerfile


def test_dockerignore_excludes_local_and_sensitive_artifacts() -> None:
    """The build context should exclude local environments and secrets."""
    ignored_entries = {
        line.strip()
        for line in read_project_file(DOCKERIGNORE).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert ".venv/" in ignored_entries
    assert ".env" in ignored_entries
    assert ".git" in ignored_entries
    assert "__pycache__/" in ignored_entries
    assert "htmlcov/" in ignored_entries
    assert "dist/" in ignored_entries


def test_dockerfile_defines_isolated_mock_target() -> None:
    """The mock service should have a dedicated image target."""
    dockerfile = read_project_file(DOCKERFILE)

    assert "FROM runtime AS mock" in dockerfile
    assert "scripts/mock_model_service.py" in dockerfile
    assert "ENV UVICORN_PORT=8001" in dockerfile
    assert "/health" in dockerfile
    assert 'CMD ["python", "-m", "uvicorn", "scripts.mock_model_service:app"]' in dockerfile


def test_dockerfile_keeps_production_as_final_target() -> None:
    """The default final image should remain the production API."""
    dockerfile = read_project_file(DOCKERFILE)

    assert dockerfile.rstrip().endswith(
        "FROM runtime AS production",
    )


def test_dockerignore_excludes_compose_from_build_context() -> None:
    """The host-side Compose file should not enter image builds."""
    ignored_entries = {
        line.strip()
        for line in read_project_file(DOCKERIGNORE).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "compose*.yaml" in ignored_entries


def test_dockerfile_uses_ephemeral_runtime_home() -> None:
    """Runtime home and temporary paths should point to writable /tmp."""
    dockerfile = read_project_file(DOCKERFILE)

    assert "HOME=/tmp" in dockerfile
    assert "TMPDIR=/tmp" in dockerfile


def test_dockerignore_excludes_container_validation_script() -> None:
    """The host-side smoke-test script should not enter image builds."""
    ignored_entries = {
        line.strip()
        for line in read_project_file(DOCKERIGNORE).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "scripts/container_smoke_test.py" in ignored_entries
