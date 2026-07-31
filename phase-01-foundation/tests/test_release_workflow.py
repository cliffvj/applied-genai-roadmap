"""Static contract tests for the Phase 1 release workflow."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RELEASE_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "phase1-release.yml"


def read_release_workflow() -> str:
    """Read the release workflow as UTF-8 text."""
    return RELEASE_WORKFLOW.read_text(
        encoding="utf-8",
    )


def test_release_workflow_is_tag_driven() -> None:
    """The release should run only after a version tag is pushed."""
    workflow = read_release_workflow()

    assert "name: Phase 1 Release" in workflow
    assert "tags:" in workflow
    assert '"v*.*.*"' in workflow
    assert "pull_request:" not in workflow
    assert "pull_request_target:" not in workflow
    assert "workflow_dispatch:" not in workflow


def test_release_workflow_declares_required_permissions() -> None:
    """Release publication and provenance should use explicit scopes."""
    workflow = read_release_workflow()

    assert "contents: write" in workflow
    assert "id-token: write" in workflow
    assert "attestations: write" in workflow
    assert "packages: write" not in workflow
    assert "write-all" not in workflow


def test_release_workflow_uses_current_action_majors() -> None:
    """The release should use the selected supported action majors."""
    workflow = read_release_workflow()

    assert "uses: actions/checkout@v7" in workflow
    assert "uses: actions/setup-python@v6" in workflow
    assert "uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0" in workflow
    assert "uses: docker/setup-buildx-action@v4" in workflow
    assert "uses: actions/attest@v4" in workflow


def test_release_workflow_checks_out_complete_tag_history() -> None:
    """The release runner should have complete tag information."""
    workflow = read_release_workflow()

    assert "fetch-depth: 0" in workflow
    assert "persist-credentials: false" in workflow


def test_release_workflow_validates_tag_and_package_version() -> None:
    """A tag should match the package's semantic version."""
    workflow = read_release_workflow()

    assert "^v[0-9]+\\.[0-9]+\\.[0-9]+$" in workflow
    assert 'release_version="${tag_name#v}"' in workflow
    assert 'Path("pyproject.toml")' in workflow
    assert "does not match package version" in workflow


def test_release_workflow_requires_committed_release_notes() -> None:
    """Each tag should have a matching committed notes document."""
    workflow = read_release_workflow()

    assert 'release_notes="releases/${tag_name}.md"' in workflow
    assert "Release notes not found" in workflow
    assert '--notes-file "${RELEASE_NOTES}"' in workflow


def test_release_workflow_uses_locked_quality_gates() -> None:
    """Release validation should use the committed lock state."""
    workflow = read_release_workflow()

    assert "uv sync --locked" in workflow
    assert "uv run --locked ruff format --check ." in workflow
    assert "uv run --locked ruff check ." in workflow
    assert "uv run --locked mypy" in workflow
    assert "scripts/test_runner.py full" in workflow


def test_release_workflow_generates_cyclonedx_sbom() -> None:
    """The locked runtime graph should be exported as CycloneDX."""
    workflow = read_release_workflow()

    assert "uv export" in workflow
    assert "--format requirements.txt" in workflow
    assert "--locked" in workflow
    assert "--no-dev" in workflow
    assert "--no-emit-project" in workflow
    assert "--no-hashes" in workflow

    assert "uv run --locked cyclonedx-py requirements" in workflow
    assert "--pyproject pyproject.toml" in workflow
    assert "--mc-type application" in workflow
    assert "--spec-version 1.5" in workflow
    assert "--output-format JSON" in workflow
    assert "--output-reproducible" in workflow
    assert "-sbom.cdx.json" in workflow
    assert "rm release-assets/runtime-requirements.txt" in workflow


def test_release_workflow_builds_both_container_targets() -> None:
    """The release should contain production and mock images."""
    workflow = read_release_workflow()

    assert "--target production" in workflow
    assert "--target mock" in workflow
    assert (
        workflow.count(
            '--platform "${IMAGE_PLATFORM}"',
        )
        == 2
    )
    assert "docker save" in workflow
    assert "linux-amd64.tar.gz" in workflow


def test_release_workflow_generates_checksums() -> None:
    """Every distributable asset should have a SHA-256 digest."""
    workflow = read_release_workflow()

    assert "sha256sum" in workflow
    assert "> SHA256SUMS" in workflow
    assert "sha256sum --check SHA256SUMS" in workflow


def test_release_workflow_attests_release_assets() -> None:
    """Release assets should receive GitHub provenance."""
    workflow = read_release_workflow()

    assert "Generate release-asset provenance" in workflow
    assert "uses: actions/attest@v4" in workflow
    assert "subject-path: phase-01-foundation/release-assets/*" in workflow
    assert "gh attestation verify" in workflow


def test_release_workflow_verifies_existing_tag() -> None:
    """The workflow should never create an implicit tag."""
    workflow = read_release_workflow()

    assert "gh release create" in workflow
    assert "--verify-tag" in workflow
    assert "--latest" in workflow


def test_release_workflow_does_not_publish_images() -> None:
    """Phase 1 releases should not receive registry credentials."""
    workflow = read_release_workflow()

    assert "docker/login-action" not in workflow
    assert "docker push" not in workflow
    assert "secrets." not in workflow
    assert "packages: write" not in workflow


def test_release_workflow_does_not_cancel_active_release() -> None:
    """A second event should not interrupt release publication."""
    workflow = read_release_workflow()

    assert "concurrency:" in workflow
    assert "cancel-in-progress: false" in workflow
