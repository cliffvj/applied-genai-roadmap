# Phase 1 — Applied GenAI Engineering Foundation

Phase 1 establishes the Python development, API, testing, automation, and documentation foundation that will support the later AI infrastructure phases.

## Objectives

By completing this phase, the project will demonstrate the ability to:

- Manage a modern Python project
- Structure maintainable application code
- Build and document REST APIs with FastAPI
- Validate API data using Pydantic
- Implement asynchronous operations
- Write automated tests
- Apply linting and static type checking
- Package the service in a container
- Validate changes through continuous integration

## Planned Commits

| Commit | Scope | Status |
|---|---|---|
| 1 | Repository and project foundation | Complete |
| 2 | Python tooling and dependency management | Complete |
| 3 | FastAPI application and REST endpoints | Complete |
| 4 | Pydantic validation and configuration | Planned |
| 5 | Async operations and external service client | Planned |
| 6 | Automated testing and quality controls | Planned |
| 7 | Containerization and health checks | Planned |
| 8 | GitHub Actions, documentation, and release | Planned |

## Planned Application

Phase 1 will produce a small API service that acts as the initial control plane for the wider roadmap.

Later phases will extend this service to support:

- Local and remote LLM inference
- Model metadata
- Retrieval-Augmented Generation
- Streaming responses
- GPU workload status
- Health and readiness checks
- Metrics and tracing

## Project Structure

```text
phase-01-foundation/
├── docs/
├── scripts/
├── src/
│   └── applied_genai/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_package.py
├── .python-version
├── pyproject.toml
├── README.md
└── uv.lock
```

## Development Toolchain

| Tool | Purpose |
|---|---|
| uv | Python runtime, virtual environment, dependency, and lock-file management |
| Python 3.12 | Project-specific Python runtime |
| Ruff | Python linting, import sorting, and formatting |
| MyPy | Static type checking |
| pytest | Automated test execution |
| pytest-cov | Test coverage measurement |
| pre-commit | Automated quality checks before Git commits |
| Hatchling | Python package build backend |

## Python Environment

The host operating system may use a different Python version. This project uses a separately managed Python 3.12 environment through `uv`.

The project version is defined in:

```text
.python-version
```

```text
3.12
```

The supported Python range is declared in `pyproject.toml`:

```toml
requires-python = ">=3.12,<3.13"
```

Synchronize the project environment from inside `phase-01-foundation`:

```powershell
uv sync --locked
```

Verify the active project interpreter:

```powershell
uv run python --version
uv run python -c "import sys; print(sys.executable)"
```

## Local Development

The simplest workflow is to run Python development commands from inside the Phase 1 directory:

```powershell
cd phase-01-foundation
```

### Run Ruff linting

```powershell
uv run ruff check .
```

Automatically apply safe lint fixes:

```powershell
uv run ruff check --fix .
```

### Run Ruff formatting

Apply formatting:

```powershell
uv run ruff format .
```

Verify formatting without changing files:

```powershell
uv run ruff format --check .
```

### Run MyPy

```powershell
uv run mypy
```

### Run pytest and coverage

```powershell
uv run pytest
```

### Build the Python package

```powershell
uv build
```

Generated distributions are placed under:

```text
dist/
```

The `dist/` directory is a generated build artifact and is not committed to Git.

## Repository-Root Commands

The repository uses a multi-phase layout. Running `uv` with `--project` selects the Phase 1 environment, but it does not change the command's working directory.

From the repository root, use explicit configuration and target paths.

### Ruff

```powershell
uv run --project phase-01-foundation ruff check phase-01-foundation
uv run --project phase-01-foundation ruff format --check phase-01-foundation
```

### MyPy

```powershell
uv run --project phase-01-foundation mypy `
  --config-file phase-01-foundation/pyproject.toml `
  phase-01-foundation/src `
  phase-01-foundation/tests
```

### pytest

```powershell
uv run --project phase-01-foundation pytest `
  -c phase-01-foundation/pyproject.toml `
  phase-01-foundation/tests
```

### Pre-commit

```powershell
uv run --project phase-01-foundation pre-commit run --all-files
```

## Pre-commit Quality Gates

The repository-level `.pre-commit-config.yaml` currently validates Phase 1 with:

- Ruff linting
- Ruff formatting
- MyPy static type checking

Install the Git hook from the repository root:

```powershell
uv run --project phase-01-foundation pre-commit install
```

Run all hooks manually:

```powershell
uv run --project phase-01-foundation pre-commit run --all-files
```

Expected result:

```text
Phase 1 - Ruff lint........................................Passed
Phase 1 - Ruff format......................................Passed
Phase 1 - MyPy type check..................................Passed
```

## Current Package Interface

The initial package exposes basic project metadata:

```python
from applied_genai import __version__, project_name

print(__version__)
print(project_name())
```

Expected output:

```text
0.1.0
Applied GenAI Foundation
```

This minimal package provides a valid target for packaging, linting, type checking, and automated tests before the FastAPI application is introduced.

## FastAPI Service

Phase 1 now includes a working FastAPI service with application metadata, health probes, versioned routing, and generated API documentation.

### Available Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Return service information |
| GET | `/health/live` | Confirm that the application process is alive |
| GET | `/health/ready` | Confirm that the API is ready to receive traffic |
| GET | `/api/v1/status` | Return versioned API operational information |
| GET | `/openapi.json` | Return the generated OpenAPI schema |
| GET | `/docs` | Open Swagger UI |
| GET | `/redoc` | Open ReDoc |

### Run the Development Server

From `phase-01-foundation`:

```powershell
uv run uvicorn applied_genai.main:app --host 127.0.0.1 --port 8000 --reload
```

Open the Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Open the ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

The development server uses automatic reload and should not be treated as the final production process configuration.

## Testing and Coverage

The initial tests validate:

- The package version
- The human-readable project name

The configured minimum test coverage is:

```text
80%
```

Run the complete test suite:

```powershell
uv run pytest
```

## Commit 2 Completion Gate

Commit 2 is ready to complete when all commands below pass from inside `phase-01-foundation`:

```powershell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv build
```

Then run the repository-level pre-commit checks:

```powershell
cd ..
uv run --project phase-01-foundation pre-commit run --all-files
```

## Status

Commits 1 through 3 are complete.

The project now includes a reproducible Python development environment, automated code-quality controls, package validation, and a tested FastAPI service with health probes, versioned routing, and OpenAPI documentation.