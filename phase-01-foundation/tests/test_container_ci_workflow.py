"""Static contract tests for the Phase 1 container CI workflow."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTAINER_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "phase1-container-ci.yml"


def read_container_workflow() -> str:
    """Read the container workflow as UTF-8 text."""
    return CONTAINER_WORKFLOW.read_text(
        encoding="utf-8",
    )


def test_container_workflow_declares_expected_triggers() -> None:
    """Container CI should run for PRs, main pushes, and manual runs."""
    workflow = read_container_workflow()

    assert "name: Phase 1 Container CI" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "      - main" in workflow


def test_container_workflow_uses_least_privilege() -> None:
    """Container validation should only require repository read access."""
    workflow = read_container_workflow()

    assert "permissions:\n  contents: read" in workflow
    assert "contents: write" not in workflow
    assert "packages: write" not in workflow
    assert "id-token: write" not in workflow
    assert "write-all" not in workflow


def test_container_workflow_avoids_elevated_pr_trigger() -> None:
    """Untrusted code should not run through pull_request_target."""
    workflow = read_container_workflow()

    assert "pull_request_target:" not in workflow


def test_container_workflow_uses_current_action_majors() -> None:
    """The workflow should use the selected action major versions."""
    workflow = read_container_workflow()

    assert "uses: actions/checkout@v7" in workflow
    assert "uses: actions/setup-python@v6" in workflow
    assert "uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0" in workflow
    assert "uses: docker/setup-buildx-action@v4" in workflow
    assert (
        workflow.count(
            "uses: docker/build-push-action@v7",
        )
        == 2
    )
    assert "uses: actions/upload-artifact@v4" in workflow


def test_container_workflow_does_not_persist_credentials() -> None:
    """Checkout credentials should not remain available to later steps."""
    workflow = read_container_workflow()

    assert "persist-credentials: false" in workflow


def test_container_workflow_uses_locked_python_environment() -> None:
    """Container validation should use committed dependency state."""
    workflow = read_container_workflow()

    assert "uv sync --locked" in workflow
    assert "uv run --locked pytest" in workflow
    assert "phase-01-foundation/uv.lock" in workflow


def test_container_workflow_validates_build_configuration() -> None:
    """The workflow should validate Compose and Dockerfile syntax."""
    workflow = read_container_workflow()

    assert "docker compose config --quiet" in workflow
    assert "docker build --check ." in workflow
    assert "tests/test_container_files.py" in workflow
    assert "tests/test_compose_files.py" in workflow


def test_container_workflow_builds_separate_targets() -> None:
    """Production and mock services should use separate build targets."""
    workflow = read_container_workflow()

    assert "target: production" in workflow
    assert "target: mock" in workflow
    assert "applied-genai-foundation:${{ env.IMAGE_VERSION }}" in workflow
    assert "applied-genai-mock-model-service:${{ env.IMAGE_VERSION }}" in workflow


def test_container_workflow_loads_but_does_not_push_images() -> None:
    """Pull-request CI should keep all images local to the runner."""
    workflow = read_container_workflow()

    assert workflow.count("load: true") == 2
    assert workflow.count("push: false") == 2
    assert "docker/login-action" not in workflow
    assert "secrets." not in workflow


def test_container_workflow_uses_separate_build_caches() -> None:
    """Production and mock image caches should use distinct scopes."""
    workflow = read_container_workflow()

    assert "scope=phase1-production" in workflow
    assert "scope=phase1-mock" in workflow
    assert workflow.count("cache-to: type=gha") == 2
    assert workflow.count("cache-from: type=gha") == 2


def test_container_workflow_runs_recovery_drill() -> None:
    """CI should run the hardened dependency recovery workflow."""
    workflow = read_container_workflow()

    assert "scripts/container_smoke_test.py" in workflow
    assert "--keep-running" in workflow


def test_container_workflow_collects_failure_diagnostics() -> None:
    """Container failures should retain logs and inspect output."""
    workflow = read_container_workflow()

    assert "Capture container diagnostics" in workflow
    assert "docker compose logs" in workflow
    assert "container-inspect.json" in workflow
    assert "phase1-container-failure-diagnostics" in workflow
    assert "if: failure()" in workflow


def test_container_workflow_always_cleans_resources() -> None:
    """Compose resources should be removed after every workflow result."""
    workflow = read_container_workflow()

    assert "Clean up Compose resources" in workflow
    assert "if: always()" in workflow
    assert "docker compose down" in workflow
    assert "--remove-orphans" in workflow
    assert "--volumes" in workflow


def test_container_workflow_has_timeout_and_concurrency() -> None:
    """Container CI should be bounded and supersede obsolete runs."""
    workflow = read_container_workflow()

    assert "timeout-minutes: 35" in workflow
    assert "concurrency:" in workflow
    assert "cancel-in-progress: true" in workflow
