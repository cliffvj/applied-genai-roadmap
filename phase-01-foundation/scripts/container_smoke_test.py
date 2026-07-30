"""Automated hardened Compose smoke test and recovery drill."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
API_BASE_URL: Final[str] = "http://127.0.0.1:8000"
HTTP_REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0

JsonObject = dict[str, object]


class SmokeTestError(RuntimeError):
    """Raised when a container validation step fails."""


def run_command(
    command: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run one command from the Phase 1 project directory."""
    print(f"+ {shlex.join(command)}")

    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=check,
        capture_output=capture_output,
        text=True,
    )


def run_compose(
    *arguments: str,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run one Docker Compose command."""
    return run_command(
        ["docker", "compose", *arguments],
        check=check,
        capture_output=capture_output,
    )


def decode_json(raw_payload: bytes) -> JsonObject:
    """Decode and validate one JSON object."""
    payload: object = json.loads(
        raw_payload.decode("utf-8"),
    )

    if not isinstance(payload, dict):
        raise SmokeTestError(
            "Expected an HTTP response containing a JSON object.",
        )

    if not all(isinstance(key, str) for key in payload):
        raise SmokeTestError(
            "Expected all JSON object keys to be strings.",
        )

    return cast(JsonObject, payload)


def request_json(
    path: str,
    *,
    method: str = "GET",
    body: Mapping[str, object] | None = None,
) -> tuple[int, JsonObject]:
    """Perform one API request and return status plus JSON body."""
    headers = {
        "Accept": "application/json",
    }
    encoded_body: bytes | None = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        encoded_body = json.dumps(
            dict(body),
        ).encode("utf-8")

    request = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        data=encoded_body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=HTTP_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            return (
                response.status,
                decode_json(response.read()),
            )
    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            decode_json(exc.read()),
        )
    except TimeoutError as exc:
        raise SmokeTestError(
            f"Request to {path} timed out after {HTTP_REQUEST_TIMEOUT_SECONDS:g} seconds.",
        ) from exc
    except urllib.error.URLError as exc:
        raise SmokeTestError(
            f"Request to {path} failed: {exc.reason}",
        ) from exc


def wait_for_json_response(
    path: str,
    *,
    expected_status: int,
    expected_payload: JsonObject,
    method: str = "GET",
    body: Mapping[str, object] | None = None,
    timeout_seconds: float = 60.0,
) -> JsonObject:
    """Wait until an API endpoint returns the expected contract."""
    deadline = time.monotonic() + timeout_seconds
    last_observation = "no response received"

    while time.monotonic() < deadline:
        try:
            status_code, payload = request_json(
                path,
                method=method,
                body=body,
            )
            last_observation = f"status={status_code}, payload={payload!r}"

            if status_code == expected_status and payload == expected_payload:
                print(
                    f"Validated {method} {path}: HTTP {status_code}",
                )
                return payload
        except SmokeTestError as exc:
            last_observation = str(exc)

        time.sleep(1)

    raise SmokeTestError(
        f"Timed out waiting for {method} {path}. Last observation: {last_observation}",
    )


def compose_container_id(service: str) -> str:
    """Return the container ID for one Compose service."""
    result = run_compose(
        "ps",
        "--all",
        "--quiet",
        service,
        capture_output=True,
    )
    container_id = result.stdout.strip()

    if not container_id:
        raise SmokeTestError(
            f"No Compose container found for {service}.",
        )

    return container_id


def inspect_value(
    service: str,
    template: str,
) -> str:
    """Read one formatted value from Docker inspect."""
    container_id = compose_container_id(service)
    result = run_command(
        [
            "docker",
            "inspect",
            "--format",
            template,
            container_id,
        ],
        capture_output=True,
    )

    return result.stdout.strip()


def wait_for_container_health(
    service: str,
    expected_status: str,
    *,
    timeout_seconds: float = 60.0,
) -> None:
    """Wait until one Compose service reaches a health state."""
    deadline = time.monotonic() + timeout_seconds
    last_status = "unknown"

    while time.monotonic() < deadline:
        last_status = inspect_value(
            service,
            "{{.State.Health.Status}}",
        )

        if last_status == expected_status:
            print(
                f"Validated {service} health: {expected_status}",
            )
            return

        time.sleep(1)

    raise SmokeTestError(
        f"{service} did not become {expected_status}. Last status: {last_status}",
    )


def assert_hardening(
    service: str,
    *,
    expected_pids: int,
    expected_memory: int,
    expected_nano_cpus: int,
) -> None:
    """Validate runtime security and resource controls."""
    if (
        inspect_value(
            service,
            "{{.HostConfig.ReadonlyRootfs}}",
        )
        != "true"
    ):
        raise SmokeTestError(
            f"{service} does not have a read-only root filesystem.",
        )

    capabilities = inspect_value(
        service,
        "{{json .HostConfig.CapDrop}}",
    )

    if "ALL" not in capabilities:
        raise SmokeTestError(
            f"{service} has not dropped all capabilities.",
        )

    security_options = inspect_value(
        service,
        "{{json .HostConfig.SecurityOpt}}",
    )

    if "no-new-privileges" not in security_options:
        raise SmokeTestError(
            f"{service} allows privilege escalation.",
        )

    if (
        inspect_value(
            service,
            "{{.HostConfig.Init}}",
        )
        != "true"
    ):
        raise SmokeTestError(
            f"{service} does not have init enabled.",
        )

    actual_pids = int(
        inspect_value(
            service,
            "{{.HostConfig.PidsLimit}}",
        ),
    )
    actual_memory = int(
        inspect_value(
            service,
            "{{.HostConfig.Memory}}",
        ),
    )
    actual_nano_cpus = int(
        inspect_value(
            service,
            "{{.HostConfig.NanoCpus}}",
        ),
    )

    if actual_pids != expected_pids:
        raise SmokeTestError(
            f"{service} PID limit is {actual_pids}; expected {expected_pids}.",
        )

    if actual_memory != expected_memory:
        raise SmokeTestError(
            f"{service} memory limit is {actual_memory}; expected {expected_memory}.",
        )

    if actual_nano_cpus != expected_nano_cpus:
        raise SmokeTestError(
            f"{service} CPU limit is {actual_nano_cpus}; expected {expected_nano_cpus}.",
        )

    print(f"Validated runtime hardening: {service}")


def assert_filesystem_controls(service: str) -> None:
    """Verify read-only root and writable ephemeral temporary storage."""
    root_write = run_compose(
        "exec",
        "-T",
        service,
        "sh",
        "-c",
        "touch /app/forbidden-write",
        check=False,
        capture_output=True,
    )

    if root_write.returncode == 0:
        raise SmokeTestError(
            f"{service} unexpectedly wrote to /app.",
        )

    temporary_write = run_compose(
        "exec",
        "-T",
        service,
        "sh",
        "-c",
        "touch /tmp/write-test && rm /tmp/write-test",
        check=False,
        capture_output=True,
    )

    if temporary_write.returncode != 0:
        raise SmokeTestError(
            f"{service} could not write to its /tmp tmpfs.",
        )

    identity = run_compose(
        "exec",
        "-T",
        service,
        "sh",
        "-c",
        'test "$(id -u)" = "10001" && test "$(id -g)" = "10001"',
        check=False,
        capture_output=True,
    )

    if identity.returncode != 0:
        raise SmokeTestError(
            f"{service} is not running as UID/GID 10001.",
        )

    print(f"Validated filesystem and identity: {service}")


def validate_healthy_stack() -> None:
    """Validate the healthy two-service application stack."""
    wait_for_container_health(
        "mock-model-service",
        "healthy",
    )
    wait_for_container_health(
        "api",
        "healthy",
    )

    assert_hardening(
        "mock-model-service",
        expected_pids=64,
        expected_memory=256 * 1024 * 1024,
        expected_nano_cpus=500_000_000,
    )
    assert_hardening(
        "api",
        expected_pids=128,
        expected_memory=512 * 1024 * 1024,
        expected_nano_cpus=1_000_000_000,
    )

    assert_filesystem_controls(
        "mock-model-service",
    )
    assert_filesystem_controls("api")

    wait_for_json_response(
        "/health/live",
        expected_status=200,
        expected_payload={
            "status": "healthy",
        },
    )
    wait_for_json_response(
        "/health/ready",
        expected_status=200,
        expected_payload={
            "status": "ready",
            "model_service": {
                "required": True,
                "status": "healthy",
            },
        },
    )
    wait_for_json_response(
        "/api/v1/model-service/status",
        expected_status=200,
        expected_payload={
            "available": True,
            "upstream": {
                "service": "local-mock-model-service",
                "status": "healthy",
            },
        },
    )


def validate_generation() -> None:
    """Validate prompt generation through container networking."""
    wait_for_json_response(
        "/api/v1/prompts/generate",
        method="POST",
        body={
            "prompt": "Explain GPU memory allocation.",
            "model_id": "qwen2.5:3b",
            "temperature": 0.2,
            "max_tokens": 256,
        },
        expected_status=200,
        expected_payload={
            "model_id": "qwen2.5:3b",
            "generated_text": ("Mock model response for: Explain GPU memory allocation."),
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 4,
                "completion_tokens": 8,
                "total_tokens": 12,
            },
        },
    )


def validate_dependency_failure_and_recovery() -> None:
    """Verify liveness, readiness failure, and dependency recovery."""
    print("Stopping mock-model-service for failure drill.")

    run_compose(
        "stop",
        "mock-model-service",
    )

    wait_for_json_response(
        "/health/live",
        expected_status=200,
        expected_payload={
            "status": "healthy",
        },
    )
    wait_for_json_response(
        "/health/ready",
        expected_status=503,
        expected_payload={
            "status": "not_ready",
            "model_service": {
                "required": True,
                "status": "unavailable",
            },
        },
    )
    wait_for_container_health(
        "api",
        "unhealthy",
        timeout_seconds=60,
    )

    print("Restarting mock-model-service.")

    run_compose(
        "start",
        "--wait",
        "--wait-timeout",
        "120",
        "mock-model-service",
    )

    wait_for_json_response(
        "/health/ready",
        expected_status=200,
        expected_payload={
            "status": "ready",
            "model_service": {
                "required": True,
                "status": "healthy",
            },
        },
        timeout_seconds=60,
    )
    wait_for_container_health(
        "api",
        "healthy",
        timeout_seconds=60,
    )

    validate_generation()


def run_smoke_test(
    *,
    build_images: bool,
    keep_running: bool,
) -> None:
    """Run the complete hardened-container validation workflow."""
    run_compose(
        "down",
        "--remove-orphans",
        check=False,
    )

    up_arguments = [
        "up",
        "--detach",
        "--wait",
        "--wait-timeout",
        "120",
        "--remove-orphans",
    ]

    if build_images:
        up_arguments.append("--build")

    try:
        run_compose(*up_arguments)

        validate_healthy_stack()
        validate_generation()
        validate_dependency_failure_and_recovery()

        print(
            "Container smoke test and recovery drill passed.",
        )
    except Exception:
        run_compose(
            "ps",
            "--all",
            check=False,
        )
        run_compose(
            "logs",
            "--no-color",
            "--tail",
            "100",
            check=False,
        )
        raise
    finally:
        if keep_running:
            print(
                "Compose stack remains running by request.",
            )
        else:
            run_compose(
                "down",
                "--remove-orphans",
                check=False,
            )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate hardened Compose containers, API contracts, "
            "dependency failure behavior, and recovery."
        ),
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build Compose images before starting the stack.",
    )
    parser.add_argument(
        "--keep-running",
        action="store_true",
        help="Leave the Compose stack running after validation.",
    )

    return parser


def main() -> int:
    """Run the requested container validation workflow."""
    parser = create_argument_parser()
    arguments = parser.parse_args()

    try:
        run_smoke_test(
            build_images=bool(arguments.build),
            keep_running=bool(arguments.keep_running),
        )
    except (
        SmokeTestError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"Container validation failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
