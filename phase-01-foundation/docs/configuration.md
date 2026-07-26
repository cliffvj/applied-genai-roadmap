# Application Configuration

The Applied GenAI Foundation service uses Pydantic Settings to load and validate runtime configuration.

Configuration is defined in:

```text
src/applied_genai/core/config.py
```

A safe configuration template is provided in:

```text
.env.example
```

## Configuration Sources

The application obtains configuration from:

1. Explicit values supplied when constructing `Settings`
2. Operating-system environment variables
3. The local `.env` file
4. Declared default values

Operating-system environment variables take priority over values from `.env`.

All project-specific environment variables use this prefix:

```text
APPLIED_GENAI_
```

## Supported Variables

| Variable | Type | Default | Validation | Purpose |
|---|---:|---|---|---|
| `APPLIED_GENAI_APP_NAME` | String | `Applied GenAI Foundation` | 1–100 characters | Human-readable service name |
| `APPLIED_GENAI_APP_VERSION` | String | `0.1.0` | Semantic version format | Running service version |
| `APPLIED_GENAI_ENVIRONMENT` | String | `development` | `development`, `test`, `staging`, or `production` | Deployment environment |
| `APPLIED_GENAI_DEBUG` | Boolean | `false` | Boolean value | Enable or disable FastAPI debug behavior |
| `APPLIED_GENAI_HOST` | String | `127.0.0.1` | Non-empty string | Intended network listener address |
| `APPLIED_GENAI_PORT` | Integer | `8000` | 1–65535 | Intended network listener port |
| `APPLIED_GENAI_DOCS_ENABLED` | Boolean | `true` | Boolean value | Enable OpenAPI, Swagger UI, and ReDoc |
| `APPLIED_GENAI_LOG_LEVEL` | String | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` | Intended application logging level |

## Local `.env` Configuration

Create a local configuration file from the example:

```bash
cp .env.example .env
```

Edit `.env` as needed:

```dotenv
APPLIED_GENAI_APP_NAME=Local GenAI Service
APPLIED_GENAI_APP_VERSION=0.1.0
APPLIED_GENAI_ENVIRONMENT=development
APPLIED_GENAI_DEBUG=true
APPLIED_GENAI_HOST=127.0.0.1
APPLIED_GENAI_PORT=8000
APPLIED_GENAI_DOCS_ENABLED=true
APPLIED_GENAI_LOG_LEVEL=DEBUG
```

The real `.env` file is ignored by Git and must not be committed.

The `.env.example` file contains only non-sensitive example values and is committed as configuration documentation.

## Validate the Loaded Settings

From `phase-01-foundation`:

```bash
uv run python -c \
  "from applied_genai.core.config import get_settings; print(get_settings().model_dump())"
```

Expected default values include:

```text
{
    'app_name': 'Applied GenAI Foundation',
    'app_version': '0.1.0',
    'environment': 'development',
    'debug': False,
    'host': '127.0.0.1',
    'port': 8000,
    'docs_enabled': True,
    'log_level': 'INFO'
}
```

## Environment-Variable Override

Git Bash example:

```bash
APPLIED_GENAI_APP_NAME="Staging GenAI Service" \
APPLIED_GENAI_APP_VERSION="1.5.0" \
APPLIED_GENAI_ENVIRONMENT="staging" \
APPLIED_GENAI_DEBUG=true \
APPLIED_GENAI_DOCS_ENABLED=false \
uv run uvicorn applied_genai.main:app \
  --host 127.0.0.1 \
  --port 8000
```

PowerShell example:

```powershell
$env:APPLIED_GENAI_APP_NAME = "Staging GenAI Service"
$env:APPLIED_GENAI_APP_VERSION = "1.5.0"
$env:APPLIED_GENAI_ENVIRONMENT = "staging"
$env:APPLIED_GENAI_DEBUG = "true"
$env:APPLIED_GENAI_DOCS_ENABLED = "false"

uv run uvicorn applied_genai.main:app `
  --host 127.0.0.1 `
  --port 8000
```

Remove the temporary PowerShell variables afterward:

```powershell
Remove-Item Env:APPLIED_GENAI_APP_NAME
Remove-Item Env:APPLIED_GENAI_APP_VERSION
Remove-Item Env:APPLIED_GENAI_ENVIRONMENT
Remove-Item Env:APPLIED_GENAI_DEBUG
Remove-Item Env:APPLIED_GENAI_DOCS_ENABLED
```

## Documentation Control

When this setting is enabled:

```dotenv
APPLIED_GENAI_DOCS_ENABLED=true
```

the following resources are available:

| Resource | Path |
|---|---|
| OpenAPI schema | `/openapi.json` |
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |

When it is disabled:

```dotenv
APPLIED_GENAI_DOCS_ENABLED=false
```

all three paths return HTTP `404`.

The root endpoint reports:

```json
{
  "documentation": null
}
```

and the versioned status endpoint reports:

```json
{
  "documentation_enabled": false
}
```

## Application Factory Integration

The FastAPI application factory accepts a validated `Settings` instance:

```python
from applied_genai.core.config import Settings
from applied_genai.main import create_app

settings = Settings(
    app_name="Test GenAI Service",
    app_version="1.0.0",
    environment="test",
    debug=False,
    docs_enabled=False,
)

application = create_app(settings)
```

The supplied settings control:

- Application title
- Application version
- Debug behavior
- OpenAPI availability
- Swagger UI availability
- ReDoc availability
- Service-information responses
- Versioned API status responses

The application binds the same settings object to FastAPI's settings dependency, keeping application metadata and endpoint responses consistent.

## Listener and Logging Settings

`APPLIED_GENAI_HOST`, `APPLIED_GENAI_PORT`, and `APPLIED_GENAI_LOG_LEVEL` are validated and available to the application.

For the current manual development command, Uvicorn command-line options still determine the actual listener address, listener port, and log level:

```bash
uv run uvicorn applied_genai.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --log-level info
```

A later phase can introduce a launch wrapper or container entrypoint that consumes these settings directly.

## Security Guidelines

- Never commit `.env`.
- Never store passwords, API tokens, cloud credentials, or private keys in `.env.example`.
- Commit only safe placeholders and configuration documentation.
- Use environment injection or an approved secrets-management system for deployed environments.
- Validate all externally supplied configuration before application startup.