"""Static contract tests for changelog and release metadata."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPOSITORY_ROOT / "phase-01-foundation"

CHANGELOG = REPOSITORY_ROOT / "CHANGELOG.md"
RELEASE_NOTES = PROJECT_ROOT / "releases" / "v0.1.0.md"
GITIGNORE = REPOSITORY_ROOT / ".gitignore"
DOCKERIGNORE = PROJECT_ROOT / ".dockerignore"


def read_text(path: Path) -> str:
    """Read one repository file as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def test_changelog_declares_initial_release() -> None:
    """The repository changelog should contain the initial version."""
    changelog = read_text(CHANGELOG)

    assert changelog.startswith("# Changelog\n")
    assert "## [Unreleased]" in changelog
    assert "## [0.1.0] - 2026-07-31" in changelog


def test_changelog_covers_phase_one_capabilities() -> None:
    """The first release should summarize all Phase 1 pillars."""
    changelog = read_text(CHANGELOG)

    assert "FastAPI Application" in changelog
    assert "Asynchronous Model-Service Integration" in changelog
    assert "Testing and Quality Controls" in changelog
    assert "Containerization" in changelog
    assert "Continuous Integration and Supply Chain" in changelog


def test_release_notes_identify_version_and_scope() -> None:
    """The notes should identify the version and Phase 1 completion."""
    notes = read_text(RELEASE_NOTES)

    assert notes.startswith(
        "# Applied GenAI Foundation v0.1.0\n",
    )
    assert "completes Phase 1" in notes


def test_release_notes_document_public_endpoints() -> None:
    """The public API contracts should be represented in the notes."""
    notes = read_text(RELEASE_NOTES)

    assert "/health/live" in notes
    assert "/health/ready" in notes
    assert "/api/v1/model-service/status" in notes
    assert "/api/v1/prompts/generate" in notes


def test_release_notes_list_every_generated_asset() -> None:
    """All release-workflow artifacts should be documented."""
    notes = read_text(RELEASE_NOTES)

    expected_assets = (
        "applied_genai_foundation-0.1.0-py3-none-any.whl",
        "applied_genai_foundation-0.1.0.tar.gz",
        "applied-genai-foundation-0.1.0-linux-amd64.tar.gz",
        ("applied-genai-mock-model-service-0.1.0-linux-amd64.tar.gz"),
        "applied-genai-foundation-0.1.0-sbom.cdx.json",
        "SHA256SUMS",
    )

    for asset in expected_assets:
        assert asset in notes


def test_release_notes_document_integrity_verification() -> None:
    """Users should receive checksum and provenance commands."""
    notes = read_text(RELEASE_NOTES)

    assert "sha256sum --check SHA256SUMS" in notes
    assert "gh attestation verify" in notes
    assert "gh release verify-asset" in notes


def test_release_notes_document_container_loading() -> None:
    """The exported image archive should have loading guidance."""
    notes = read_text(RELEASE_NOTES)

    assert "docker load" in notes
    assert "gunzip -c" in notes


def test_release_notes_state_current_limitations() -> None:
    """Phase 1 limitations should be explicit."""
    notes = read_text(RELEASE_NOTES)

    assert "non-streaming" in notes
    assert "Linux AMD64 only" in notes
    assert "not yet published to a container registry" in notes
    assert "NVIDIA Container Toolkit" in notes


def test_release_metadata_has_no_unresolved_placeholders() -> None:
    """Committed release metadata should contain no editing markers."""
    combined_metadata = read_text(CHANGELOG) + "\n" + read_text(RELEASE_NOTES)

    forbidden_markers = (
        "TODO",
        "TBD",
        "FIXME",
        "INSERT RELEASE",
    )

    for marker in forbidden_markers:
        assert marker not in combined_metadata


def test_generated_release_assets_are_ignored() -> None:
    """Generated asset directories should not enter Git or images."""
    gitignore = read_text(GITIGNORE)
    dockerignore = read_text(DOCKERIGNORE)

    assert "phase-01-foundation/release-assets/" in gitignore
    assert "release-assets/" in dockerignore
