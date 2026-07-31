"""Static contract tests for the repository Dependabot policy."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEPENDABOT_CONFIG = REPOSITORY_ROOT / ".github" / "dependabot.yml"


def read_dependabot_config() -> str:
    """Read the Dependabot configuration as UTF-8 text."""
    return DEPENDABOT_CONFIG.read_text(
        encoding="utf-8",
    )


def test_dependabot_uses_supported_configuration_version() -> None:
    """Dependabot should use the current configuration schema."""
    config = read_dependabot_config()

    assert config.startswith("version: 2\n")
    assert "updates:" in config


def test_dependabot_manages_uv_dependencies() -> None:
    """The Phase 1 uv project should receive dependency updates."""
    config = read_dependabot_config()

    assert "package-ecosystem: uv" in config
    assert "directory: /phase-01-foundation" in config
    assert "python-minor-and-patch:" in config


def test_dependabot_uses_uv_instead_of_legacy_pip_policy() -> None:
    """The repository should use Dependabot's native uv ecosystem."""
    config = read_dependabot_config()

    assert "package-ecosystem: pip" not in config


def test_dependabot_manages_github_actions() -> None:
    """Workflow actions should receive automated update pull requests."""
    config = read_dependabot_config()

    assert "package-ecosystem: github-actions" in config
    assert "directory: /" in config
    assert "prefix: ci" in config


def test_dependabot_manages_dockerfile_images() -> None:
    """Pinned Dockerfile images should receive automated updates."""
    config = read_dependabot_config()

    assert "package-ecosystem: docker" in config
    assert "prefix: build" in config


def test_dependabot_uses_predictable_weekly_schedules() -> None:
    """Each ecosystem should run on a known weekday and timezone."""
    config = read_dependabot_config()

    assert config.count("interval: weekly") == 3
    assert "day: monday" in config
    assert "day: tuesday" in config
    assert "day: wednesday" in config
    assert config.count("timezone: Asia/Manila") == 3


def test_dependabot_limits_version_update_noise() -> None:
    """Open version-update pull requests should remain bounded."""
    config = read_dependabot_config()

    assert (
        config.count(
            "open-pull-requests-limit:",
        )
        == 3
    )
    assert "open-pull-requests-limit: 5" in config
    assert "open-pull-requests-limit: 3" in config


def test_dependabot_applies_release_cooldowns() -> None:
    """New dependency releases should observe stabilization periods."""
    config = read_dependabot_config()

    assert config.count("cooldown:") == 3
    assert config.count("default-days: 7") == 3
    assert "semver-major-days: 14" in config
    assert "semver-minor-days: 7" in config
    assert "semver-patch-days: 3" in config


def test_dependabot_does_not_define_private_registries() -> None:
    """The public project should not contain registry credentials."""
    config = read_dependabot_config()

    assert "registries:" not in config
    assert "username:" not in config
    assert "password:" not in config
    assert "token:" not in config


def test_dependabot_targets_the_default_branch() -> None:
    """Security updates should retain default-branch behavior."""
    config = read_dependabot_config()

    assert "target-branch:" not in config
