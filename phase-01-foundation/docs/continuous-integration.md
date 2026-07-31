# Continuous Integration and Release Automation

The Applied GenAI Foundation project uses GitHub Actions for Python quality validation, container testing, release packaging, and supply-chain provenance.

The automation is divided into three workflows:

| Workflow | Trigger | Responsibility |
|---|---|---|
| `phase1-ci.yml` | Pull requests, main pushes, manual runs | Python quality, tests, coverage, and package artifacts |
| `phase1-container-ci.yml` | Pull requests, main pushes, manual runs | Container builds, hardening validation, failure drills, and recovery |
| `phase1-release.yml` | Semantic-version Git tags | Release assets, checksums, SBOM, provenance, and GitHub Release publication |

## Security Model

The validation workflows use:

```yaml
permissions:
  contents: read
```

They do not receive:

- Repository write access
- Package publication access
- OIDC token access
- Attestation write access
- Registry credentials
- Repository secrets

Checkout credentials are not retained:

```yaml
persist-credentials: false
```

Neither pull-request workflow uses:

```text
pull_request_target
```

This prevents untrusted pull-request code from running with elevated repository permissions.

## Python CI

The Python workflow runs:

1. Locked dependency synchronization
2. Ruff formatting validation
3. Ruff linting
4. Strict MyPy validation
5. Full serial tests
6. Full parallel tests
7. Python package builds
8. Package artifact upload
9. HTML coverage artifact upload

The workflow uses the committed `uv.lock` file:

```bash
uv sync --locked
```

The workflow does not re-resolve dependencies.

### Uploaded Artifacts

A successful Python CI run uploads:

```text
applied-genai-foundation-package
applied-genai-foundation-coverage
```

Package artifacts are retained for 14 days.

Coverage reports are retained for seven days.

## Container CI

The container workflow validates:

- Dockerfile syntax and build checks
- Docker Compose configuration
- Static container contract tests
- Production and mock image isolation
- Non-root runtime execution
- Read-only root filesystems
- Writable ephemeral temporary storage
- Dropped Linux capabilities
- Prevention of privilege escalation
- CPU, memory, and PID limits
- Container health checks
- Internal service networking
- Dependency failure behavior
- Readiness failure
- Container unhealthy transitions
- Dependency recovery
- Prompt generation after recovery

The workflow builds two targets:

```text
production
mock
```

Images are loaded only into the temporary GitHub-hosted runner.

The pull-request workflow does not:

```text
log in to a registry
push container images
request packages: write
read repository secrets
```

## Failure Diagnostics

When container validation fails, the workflow captures:

```text
compose-ps.txt
compose-logs.txt
container-inspect.json
image-inspect.json
```

These files are uploaded as:

```text
phase1-container-failure-diagnostics
```

Compose resources are removed regardless of success or failure.

## Build Caching

The production and mock images use separate GitHub Actions cache scopes:

```text
phase1-production
phase1-mock
```

Separating these caches avoids one target overwriting the other target's cached build state.

## Dependabot

Dependabot manages three ecosystems:

| Ecosystem | Directory | Schedule |
|---|---|---|
| uv | `/phase-01-foundation` | Monday |
| GitHub Actions | `/` | Tuesday |
| Docker | `/phase-01-foundation` | Wednesday |

All schedules use:

```text
Asia/Manila
09:00
```

Version-update pull requests are bounded to reduce repository noise.

Cooldown periods allow newly published dependency versions to stabilize before routine update pull requests are opened.

Security updates continue to follow GitHub's security-update behavior.

## Release Workflow

The release workflow runs only for tags matching:

```text
v*.*.*
```

The workflow additionally validates the stricter form:

```text
vMAJOR.MINOR.PATCH
```

For example:

```text
v0.1.0
```

The tag version must match:

```toml
[project]
version = "0.1.0"
```

The release also requires a committed notes file:

```text
releases/v0.1.0.md
```

## Release Quality Gate

Before producing assets, the workflow runs:

- Locked environment synchronization
- Ruff formatting validation
- Ruff linting
- Strict MyPy validation
- Full serial pytest profile
- Docker Compose validation
- Dockerfile build validation

A quality-gate failure prevents release publication.

## Release Assets

The `v0.1.0` workflow creates:

| Asset | Purpose |
|---|---|
| Python wheel | Installable binary Python distribution |
| Python source archive | Source distribution |
| Production container archive | Offline Linux AMD64 API image |
| Mock-service container archive | Offline Linux AMD64 mock image |
| CycloneDX SBOM | Runtime dependency inventory |
| `SHA256SUMS` | Integrity manifest |

The container archives are compressed reproducibly using:

```bash
gzip --best --no-name
```

## SBOM Generation

The project uses uv to export the locked runtime dependency graph:

```bash
uv export \
  --format requirements.txt \
  --locked \
  --no-dev \
  --no-emit-project \
  --no-hashes
```

The pinned CycloneDX Python tool converts that graph into a reproducible CycloneDX 1.5 JSON SBOM.

The temporary requirements export is not included as a release asset.

## Checksums

The release workflow creates:

```text
SHA256SUMS
```

Validate downloaded assets with:

```bash
sha256sum --check SHA256SUMS
```

Every listed asset should return:

```text
OK
```

## Artifact Provenance

GitHub artifact attestations are generated for the release assets.

The workflow requires:

```yaml
permissions:
  contents: write
  id-token: write
  attestations: write
```

The release workflow does not receive package-registry credentials because Phase 1 exports image archives instead of publishing container images.

## GitHub Release Publication

The workflow creates the release only when the Git tag already exists:

```bash
gh release create \
  v0.1.0 \
  --verify-tag
```

This prevents the workflow from implicitly creating a missing tag.

The release notes come from:

```text
phase-01-foundation/releases/v0.1.0.md
```

## Local Quality Parity

Run the Python gates:

```bash
uv sync --locked
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy
uv run --locked python scripts/test_runner.py full
uv run --locked python scripts/test_runner.py parallel
uv build
```

Run the container gates:

```bash
docker compose config --quiet
docker build --check .

uv run --locked python \
  scripts/container_smoke_test.py \
  --build
```

Run repository pre-commit checks:

```bash
uv run --project phase-01-foundation --locked \
  pre-commit run --all-files
```

## Release Sequence

The supported release sequence is:

1. Complete and validate the release commit.
2. Push `main`.
3. Wait for Python CI to pass.
4. Wait for container CI to pass.
5. Create an annotated version tag.
6. Push the version tag.
7. Wait for the release workflow.
8. Verify the published release and assets.

The version tag must not be pushed before the main-branch validation workflows have passed.

## Current Limitations

Phase 1 automation does not yet provide:

- Container registry publication
- Multi-architecture container images
- Signed Git tags
- PyPI publication
- Automatic version bumping
- Release promotion environments
- Deployment environments
- Kubernetes validation
- GPU runner validation
- NVIDIA Container Toolkit testing
- Runtime vulnerability scanning

These capabilities are reserved for later CI/CD, deployment, security, and GPU infrastructure phases.