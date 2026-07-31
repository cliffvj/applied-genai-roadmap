"""Static contract tests for the Phase 1 GitHub Actions workflow."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "phase1-ci.yml"


def read_ci_workflow() -> str:
    """Read the Phase 1 CI workflow as UTF-8 text."""
    return CI_WORKFLOW.read_text(encoding="utf-8")


def test_ci_workflow_declares_expected_triggers() -> None:
    """CI should run for pull requests, main pushes, and manual runs."""
    workflow = read_ci_workflow()

    assert "name: Phase 1 CI" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "      - main" in workflow


def test_ci_workflow_uses_least_privilege_permissions() -> None:
    """The CI token should only require repository read access."""
    workflow = read_ci_workflow()

    assert "permissions:\n  contents: read" in workflow
    assert "write-all" not in workflow
    assert "contents: write" not in workflow
    assert "pull-requests: write" not in workflow


def test_ci_workflow_avoids_privileged_pull_request_target() -> None:
    """Untrusted pull-request code should not use elevated triggers."""
    workflow = read_ci_workflow()

    assert "pull_request_target:" not in workflow


def test_ci_workflow_uses_stable_linux_runner() -> None:
    """Phase 1 CI should run on the declared stable Linux image."""
    workflow = read_ci_workflow()

    assert "runs-on: ubuntu-24.04" in workflow
    assert "timeout-minutes: 20" in workflow


def test_ci_workflow_uses_current_action_majors() -> None:
    """CI should use the selected supported action major versions."""
    workflow = read_ci_workflow()

    assert "uses: actions/checkout@v7" in workflow
    assert "uses: actions/setup-python@v6" in workflow
    assert "uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0" in workflow
    assert (
        workflow.count(
            "uses: actions/upload-artifact@v4",
        )
        == 2
    )


def test_ci_workflow_does_not_persist_checkout_credentials() -> None:
    """Read-only CI should not retain its checkout token."""
    workflow = read_ci_workflow()

    assert "persist-credentials: false" in workflow


def test_ci_workflow_pins_project_tool_versions() -> None:
    """CI should match the project's Python and uv versions."""
    workflow = read_ci_workflow()

    assert 'PYTHON_VERSION: "3.12.13"' in workflow
    assert 'UV_VERSION: "0.12.0"' in workflow
    assert "version: ${{ env.UV_VERSION }}" in workflow


def test_ci_workflow_uses_locked_dependency_state() -> None:
    """CI should not modify or re-resolve the committed lockfile."""
    workflow = read_ci_workflow()

    assert "uv sync --locked" in workflow
    assert "uv run --locked ruff" in workflow
    assert "uv run --locked mypy" in workflow
    assert "phase-01-foundation/uv.lock" in workflow


def test_ci_workflow_runs_all_python_quality_gates() -> None:
    """CI should enforce formatting, linting, typing, and tests."""
    workflow = read_ci_workflow()

    assert "ruff format --check ." in workflow
    assert "ruff check ." in workflow
    assert "uv run --locked mypy" in workflow
    assert "scripts/test_runner.py full" in workflow
    assert "scripts/test_runner.py parallel" in workflow


def test_ci_workflow_builds_and_uploads_package() -> None:
    """A successful workflow should preserve distributable artifacts."""
    workflow = read_ci_workflow()

    assert "uv build" in workflow
    assert "applied-genai-foundation-package" in workflow
    assert "phase-01-foundation/dist/*" in workflow
    assert "if-no-files-found: error" in workflow


def test_ci_workflow_uploads_coverage_report() -> None:
    """The generated HTML coverage report should be retained."""
    workflow = read_ci_workflow()

    assert "applied-genai-foundation-coverage" in workflow
    assert "phase-01-foundation/htmlcov/" in workflow
    assert "retention-days: 7" in workflow


def test_ci_workflow_prevents_redundant_runs() -> None:
    """New commits should supersede obsolete runs for the same ref."""
    workflow = read_ci_workflow()

    assert "concurrency:" in workflow
    assert "github.workflow" in workflow
    assert "github.ref" in workflow
    assert "cancel-in-progress: true" in workflow
