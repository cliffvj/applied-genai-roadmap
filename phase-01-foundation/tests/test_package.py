"""Tests for the root Applied GenAI package."""

from applied_genai import __version__, project_name


def test_project_name() -> None:
    """The package should expose its human-readable project name."""
    assert project_name() == "Applied GenAI Foundation"


def test_package_version() -> None:
    """The package should expose its current semantic version."""
    assert __version__ == "0.1.0"
