"""Cross-platform test profiles and test-artifact cleanup."""

import argparse
import os
import shutil
from pathlib import Path
from typing import Final

import pytest

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

COVERAGE_FILES: Final[tuple[Path, ...]] = (
    PROJECT_ROOT / ".coverage",
    PROJECT_ROOT / "coverage.xml",
    PROJECT_ROOT / "coverage.json",
    PROJECT_ROOT / "coverage.lcov",
)

TEST_ARTIFACT_DIRECTORIES: Final[tuple[Path, ...]] = (
    PROJECT_ROOT / "htmlcov",
    PROJECT_ROOT / ".pytest_cache",
)

TEST_PROFILES: Final[dict[str, list[str]]] = {
    "fast": [
        "-m",
        "not property and not slow",
        "--no-cov",
        "--maxfail=1",
        "-q",
    ],
    "full": [],
    "parallel": [
        "-n",
        "auto",
        "--dist=loadfile",
    ],
}


def remove_artifact(path: Path) -> bool:
    """Remove one generated file or directory when it exists."""
    if path.is_dir():
        shutil.rmtree(path)
        return True

    if path.is_file():
        path.unlink()
        return True

    return False


def clean_test_artifacts() -> None:
    """Remove generated coverage reports and pytest cache data."""
    removed_paths: list[Path] = []

    for path in COVERAGE_FILES:
        if remove_artifact(path):
            removed_paths.append(path)

    for path in PROJECT_ROOT.glob(".coverage.*"):
        if remove_artifact(path):
            removed_paths.append(path)

    for path in TEST_ARTIFACT_DIRECTORIES:
        if remove_artifact(path):
            removed_paths.append(path)

    if not removed_paths:
        print("No generated test artifacts found.")
        return

    print("Removed generated test artifacts:")

    for path in removed_paths:
        print(f"- {path.relative_to(PROJECT_ROOT)}")


def run_test_profile(profile: str) -> int:
    """Run the selected pytest profile from the project root."""
    pytest_arguments = TEST_PROFILES[profile]

    if profile in {"full", "parallel"}:
        clean_test_artifacts()

    print(f"Running pytest profile: {profile}")

    if pytest_arguments:
        print(f"Arguments: {' '.join(pytest_arguments)}")
    else:
        print("Arguments: project defaults")

    return int(pytest.main(pytest_arguments))


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the test-runner command-line parser."""
    parser = argparse.ArgumentParser(
        description=("Run repeatable Phase 1 pytest profiles or remove generated test artifacts."),
    )

    parser.add_argument(
        "command",
        choices=(
            "fast",
            "full",
            "parallel",
            "clean",
        ),
        help="Test profile or cleanup operation to execute.",
    )

    return parser


def main() -> int:
    """Execute the requested test-runner command."""
    parser = create_argument_parser()
    arguments = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    if arguments.command == "clean":
        clean_test_artifacts()
        return 0

    return run_test_profile(arguments.command)


if __name__ == "__main__":
    raise SystemExit(main())
