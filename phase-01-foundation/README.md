# Phase 1 — Applied GenAI Engineering Foundation

Phase 1 establishes the Python development, API, validation, testing, automation, and documentation foundation that will support the later AI infrastructure phases.

## Objectives

By completing this phase, the project will demonstrate the ability to:

- Manage a modern Python project
- Structure maintainable application code
- Build and document REST APIs with FastAPI
- Define validated API contracts using Pydantic
- Load and validate environment-based application settings
- Implement asynchronous operations
- Write automated tests
- Apply linting and static type checking
- Package the service for distribution
- Validate changes through continuous integration

## Planned Commits

| Commit | Scope | Status |
|---|---|---|
| 1 | Repository and project foundation | Complete |
| 2 | Python tooling and dependency management | Complete |
| 3 | FastAPI application and REST endpoints | Complete |
| 4 | Pydantic models and application configuration | Complete |
| 5 | Async operations and external service client | Planned |
| 6 | Automated testing and quality controls | Planned |
| 7 | Containerization and health checks | Planned |
| 8 | GitHub Actions, documentation, and release | Planned |

## Planned Application

Phase 1 produces a small API service that acts as the initial control plane for the wider roadmap.

Later phases will extend this service to support:

- Local and remote LLM inference
- Model metadata and discovery
- Retrieval-Augmented Generation
- Streaming responses
- GPU workload status
- Dependency-aware readiness checks
- Metrics and distributed tracing

## Project Structure

```text
phase-01-foundation/
├── docs/
│   └── configuration.md
├── scripts/
├── src/
│   └── applied_genai/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── prompts.py
│       │       └── system.py
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py
│       └── schemas/
│           ├── __init__.py
│           ├── base.py
│           ├── prompt.py
│           └── system.py
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_main.py
│   ├── test_package.py
│   ├── test_prompt_routes.py
│   ├── test_prompt_schemas.py
│   ├── test_settings_integration.py
│   ├── test_system_routes.py
│   └── test_system_schemas.py
├── .env.example
├── .python-version
├── pyproject.toml
├── README.md
└── uv.lock
```

Generated directories such as `.venv`, `dist`, `htmlcov`, and Python tool caches are ignored by Git.

## Development Toolchain

| Tool | Purpose |
|---|---|
| uv | Python runtime, environment, dependency, lock-file, and build management |
| Python 3.12 | Project-specific Python runtime |
| FastAPI | ASGI API framework and OpenAPI generation |
| Uvicorn | Local ASGI development server |
| Pydantic | Runtime request, response, and field validation |
| Pydantic Settings | Environment-variable and dotenv configuration |
| python-dotenv | Dotenv file support |
| Ruff | Python linting, import sorting, and formatting |
| MyPy | Strict static type checking |
| pytest | Automated test execution |
| pytest-cov | Test coverage measurement |
| httpx2 | Test-client HTTP transport |
| pre-commit | Automated local quality checks before Git commits |
| Hatchling | Python package build backend |

## Python Environment

The host operating system may use another Python version. This project uses Python 3.12 through `uv`.

The project runtime is selected by:

```text
.python-version
```

```text
3.12
```

The supported version range is declared in `pyproject.toml`:

```toml
requires-python = ">=3.12,<3.13"
```

Synchronize the environment:

```bash
uv sync --locked
```

Verify the project interpreter:

```bash
uv run python --version
uv run python -c "import sys; print(sys.executable)"
```

## FastAPI Service

The project includes a working FastAPI service with:

- Application metadata
- Application factory
- Versioned routing
- Liveness and readiness probes
- Pydantic request and response schemas
- Validated prompt-request contracts
- Environment-aware settings
- Conditional OpenAPI and interactive documentation

### Available Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Return configured service information |
| `GET` | `/health/live` | Confirm that the application process is alive |
| `GET` | `/health/ready` | Confirm that the API is ready to receive traffic |
| `GET` | `/api/v1/status` | Return versioned runtime and environment information |
| `POST` | `/api/v1/prompts/validate` | Validate and normalize a future model request |
| `GET` | `/openapi.json` | Return the generated OpenAPI schema |
| `GET` | `/docs` | Open Swagger UI |
| `GET` | `/redoc` | Open ReDoc |

The prompt-validation endpoint validates an inference contract but does not call a language model. External asynchronous model communication will be introduced in Commit 5.

## Pydantic API Contracts

The shared API schema configuration:

- Rejects undeclared fields
- Strips surrounding whitespace from strings
- Applies reusable string and numeric constraints
- Generates JSON Schema metadata for OpenAPI
- Validates response structures before serialization

Current models include:

| Model | Purpose |
|---|---|
| `ServiceInformation` | Root service metadata |
| `HealthResponse` | Liveness and readiness responses |
| `ApiStatusResponse` | Versioned runtime status |
| `PromptRequest` | Validated future inference request |
| `PromptValidationResponse` | Normalized validation result |

### Prompt Constraints

The `PromptRequest` model currently validates:

- Non-empty prompt text
- Prompt length up to 4,000 characters
- Optional system prompt up to 2,000 characters
- Model identifier syntax
- Temperature between `0.0` and `2.0`
- Maximum token count between `1` and `4096`
- No more than eight stop sequences
- Unique normalized stop sequences
- Rejection of undeclared request fields

### Prompt Validation Example

Start the service and submit:

```bash
curl -s \
  -X POST \
  http://127.0.0.1:8000/api/v1/prompts/validate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "  Explain GPU memory allocation for LLM inference.  ",
    "model_id": "qwen2.5:3b",
    "temperature": 0.2,
    "max_tokens": 512,
    "stop_sequences": ["END"]
  }'
```

Expected response:

```json
{
  "valid": true,
  "request": {
    "prompt": "Explain GPU memory allocation for LLM inference.",
    "model_id": "qwen2.5:3b",
    "system_prompt": null,
    "temperature": 0.2,
    "max_tokens": 512,
    "stop_sequences": [
      "END"
    ]
  }
}
```

Invalid requests receive an HTTP `422` validation response.

## Application Configuration

Runtime settings are defined in:

```text
src/applied_genai/core/config.py
```

A safe configuration template is provided in:

```text
.env.example
```

Supported settings include:

- Application name and version
- Deployment environment
- Debug behavior
- Intended host and port
- API documentation availability
- Intended log level

Read the full reference:

[Application Configuration](docs/configuration.md)

## Run the Development Server

From `phase-01-foundation`:

```bash
uv run uvicorn applied_genai.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

Open:

```text
Swagger UI: http://127.0.0.1:8000/docs
ReDoc:      http://127.0.0.1:8000/redoc
OpenAPI:    http://127.0.0.1:8000/openapi.json
```

The reload option is intended for local development and is not the final production process strategy.

## Local Quality Commands

Run these commands from `phase-01-foundation`.

### Synchronize Dependencies

```bash
uv sync --locked
```

### Apply Formatting

```bash
uv run ruff format .
```

### Run Linting

```bash
uv run ruff check .
```

### Verify Formatting

```bash
uv run ruff format --check .
```

### Run Static Type Checking

```bash
uv run mypy
```

### Run Tests and Coverage

```bash
uv run pytest
```

### Build the Package

```bash
uv build
```

Build artifacts are written to `dist/` and are not committed.

## Repository-Level Pre-commit Gate

From the repository root:

```bash
uv run --project phase-01-foundation \
  pre-commit run --all-files
```

Configured hooks currently run:

- Ruff linting
- Ruff formatting verification
- MyPy strict type checking

## Testing

The automated suite validates:

- Package metadata
- Application construction
- FastAPI metadata
- OpenAPI, Swagger UI, and ReDoc
- Liveness and readiness endpoints
- Versioned status responses
- Pydantic system schemas
- Pydantic prompt schemas
- Valid and invalid prompt requests
- Environment-variable settings
- Settings defaults and constraints
- Settings caching
- Application-factory settings integration
- FastAPI dependency overrides
- Conditional documentation endpoints
- Unknown-route behavior

The configured minimum coverage threshold is:

```text
80%
```

The current suite exceeds this requirement.

## Package Interface

The package exposes basic project metadata:

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

## Status

Commits 1 through 4 are complete.

The project now includes a reproducible Python environment, automated quality controls, a packaged FastAPI service, versioned API routes, health probes, strict Pydantic request and response contracts, validated application settings, environment-aware application construction, dependency injection, and generated OpenAPI documentation.