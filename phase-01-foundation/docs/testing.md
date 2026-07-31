# Automated Testing and Quality Controls

The Applied GenAI Foundation project uses layered automated testing and strict quality controls to detect regressions before code is committed or pushed.

## Testing Stack

| Tool | Responsibility |
|---|---|
| pytest | Test collection and execution |
| pytest-cov | Statement and branch coverage |
| pytest-xdist | Parallel test execution |
| pytest-timeout | Per-test and session timeout protection |
| Hypothesis | Property-based testing and generated edge cases |
| Ruff | Python linting and formatting |
| MyPy | Strict static type checking |
| pre-commit | Automated local quality gates |

## Quality Requirements

The test configuration enforces:

- Strict pytest configuration
- Strict marker registration
- Strict parametrization identifiers
- Strict expected-failure handling
- Warnings treated as errors
- A 15-second per-test timeout
- A 180-second test-session timeout
- Branch coverage
- A minimum total coverage threshold of 95%

## Test Classifications

Tests are classified centrally in `tests/conftest.py`.

| Marker | Purpose |
|---|---|
| `unit` | Isolated function, schema, or client behavior |
| `integration` | Interaction between multiple application components |
| `contract` | API and external-service contract validation |
| `property` | Hypothesis-generated boundary and invariant testing |
| `slow` | Tests excluded from the fast development profile |

Any new `test_*.py` module must be added to `TEST_MODULE_MARKERS`.

Unclassified test modules cause collection to fail.

## Shared Test Factories

Reusable deterministic objects are defined in:

```text
tests/factories.py
```

The factories create:

- Application settings without reading a local `.env`
- Valid prompt payloads
- Validated prompt requests
- External service health responses
- External model generation responses

Preventing test settings from reading local environment files makes the suite reproducible across developer machines and CI workers.

## Property-Based Testing

Hypothesis generates valid and invalid values across the declared schema domains.

Current properties include:

- Prompt whitespace normalization
- Temperature and token-limit boundaries
- Duplicate stop-sequence rejection
- Token-usage arithmetic invariants
- Retry minimum and maximum relationships
- TCP port boundaries
- Model-service URL normalization
- External response JSON round trips
- Public generation-response JSON round trips

Strategies must generate values that satisfy the same domain represented by the schema.

For example, model identifiers are generated from:

```text
[A-Za-z0-9][A-Za-z0-9._:/-]*
```

This avoids incorrectly treating Unicode letters as valid ASCII model identifiers.

## Test Profiles

The cross-platform runner is:

```text
scripts/test_runner.py
```

### Fast Profile

```bash
uv run python scripts/test_runner.py fast
```

The fast profile:

- Excludes property-based tests
- Excludes slow tests
- Disables coverage
- Stops after the first failure
- Is suitable for pre-commit validation

### Full Profile

```bash
uv run python scripts/test_runner.py full
```

The full profile:

- Removes stale coverage artifacts
- Runs all tests serially
- Executes Hypothesis properties
- Measures statement and branch coverage
- Enforces the 95% coverage requirement
- Creates an HTML coverage report

### Parallel Profile

```bash
uv run python scripts/test_runner.py parallel
```

The parallel profile:

- Uses pytest-xdist
- Runs with two deterministic workers
- Uses `--dist=loadfile`
- Keeps tests from the same module on one worker
- Enforces the complete coverage requirement

The fixed worker count avoids changing test behavior according to the number of CPU cores on each workstation.

### Cleanup Profile

```bash
uv run python scripts/test_runner.py clean
```

The cleanup profile removes:

- `.coverage`
- `.coverage.*`
- `coverage.xml`
- `coverage.json`
- `coverage.lcov`
- `htmlcov/`
- `.pytest_cache/`

It deliberately preserves the Hypothesis examples database.

## Direct pytest Commands

Run the complete suite:

```bash
uv run pytest
```

Run with two parallel workers:

```bash
uv run pytest -n auto --dist=loadfile
```

Run only unit tests:

```bash
uv run pytest -m unit --no-cov
```

Run only integration tests:

```bash
uv run pytest -m integration --no-cov
```

Run only contract tests:

```bash
uv run pytest -m contract --no-cov
```

Run only property tests:

```bash
uv run pytest -m property --no-cov
```

Run example-based tests without property or slow tests:

```bash
uv run pytest \
  -m "not property and not slow" \
  --no-cov
```

Partial selections use `--no-cov` because they are not expected to cover the entire application.

## Debugging Failures

Disable xdist:

```bash
uv run pytest -n 0
```

Run one test module:

```bash
uv run pytest \
  tests/test_model_service_client.py \
  --no-cov
```

Run one test:

```bash
uv run pytest \
  tests/test_model_service_client.py::test_model_service_health_success \
  --no-cov
```

Show detailed output:

```bash
uv run pytest -vv --showlocals
```

Replay a Hypothesis failure by rerunning the same property test. Hypothesis stores useful examples in its local examples database.

## Pre-Commit Testing

The pre-commit configuration runs:

- Ruff linting
- Ruff formatting validation
- MyPy strict type checking
- The fast pytest profile

Run all hooks manually:

```bash
uv run --project phase-01-foundation --locked \
  pre-commit run --all-files
```

The fast profile is used during pre-commit to keep local commits responsive.

The full serial and parallel profiles remain required before completing a project commit.

## Recommended Development Workflow

Before committing:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy
uv run python scripts/test_runner.py fast
```

Before completing a feature commit:

```bash
uv run python scripts/test_runner.py full
uv run python scripts/test_runner.py parallel
uv build
```

From the repository root:

```bash
uv run --project phase-01-foundation --locked \
  pre-commit run --all-files
```

## Continuous Integration

The repository applies the same core quality controls through GitHub Actions.

### Python CI

The Python workflow runs:

- Locked environment synchronization
- Ruff formatting checks
- Ruff linting
- Strict MyPy validation
- Full serial testing
- Full parallel testing
- Python package builds
- Coverage artifact collection

### Container CI

The container workflow runs:

- Dockerfile and Compose validation
- Static container contracts
- Production and mock image builds
- Image-content isolation checks
- Hardened runtime validation
- Dependency outage simulation
- Readiness and health-state validation
- Dependency recovery
- Prompt generation after recovery

### Release Validation

The release workflow repeats the locked quality gates before creating release assets.

A release is not published when formatting, linting, typing, tests, container validation, packaging, checksums, SBOM generation, or provenance generation fails.

Read the complete guide:

[Continuous Integration and Release Automation](continuous-integration.md)

## Generated Artifacts

The following generated artifacts must not be committed:

```text
.coverage
.coverage.*
htmlcov/
.pytest_cache/
.hypothesis/
```

The Hypothesis database may remain on the developer workstation but is ignored by Git.

## Current Coverage Target

The minimum project-wide coverage requirement is:

```text
95%
```

Both statement and branch coverage are enabled.

The threshold is intended to prevent coverage regression while still allowing defensive code paths that are impractical or unsafe to force through artificial tests.