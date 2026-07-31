# Changelog

All notable changes to the Applied GenAI Roadmap are documented in this file.

The project follows semantic versioning for packaged Phase 1 releases.

## [Unreleased]

No unreleased changes are currently documented.

## [0.1.0] - 2026-07-31

### Added

#### Repository and Python Foundation

- Phase-oriented Applied GenAI engineering roadmap
- Python 3.12 project managed by uv
- Locked and reproducible dependency environment
- Hatchling package build configuration
- Ruff linting and formatting
- Strict MyPy static type checking
- Pre-commit quality gates

#### FastAPI Application

- FastAPI application factory
- Root service-information endpoint
- Liveness and dependency-aware readiness endpoints
- Versioned API status endpoint
- Interactive OpenAPI documentation
- Environment-controlled documentation availability

#### Validation and Configuration

- Strict Pydantic request and response contracts
- Environment-based application settings
- Dotenv support for local development
- Prompt validation and normalization
- Token-usage consistency validation
- External-service contract validation

#### Asynchronous Model-Service Integration

- Lifespan-managed asynchronous HTTP client
- Connection pooling and bounded timeouts
- Tenacity retry handling
- Retryable and non-retryable failure classification
- Model-service health endpoint
- Prompt-generation endpoint
- HTTP 502 and HTTP 503 error mapping
- Deterministic local mock model service

#### Testing and Quality Controls

- Centrally classified pytest suite
- Unit, integration, contract, property, and slow markers
- Deterministic test factories
- Hypothesis property-based testing
- pytest-xdist parallel execution
- Per-test and session timeout protection
- Branch coverage
- Minimum 95% project coverage
- Fast, full, parallel, and cleanup test profiles

#### Containerization

- Multi-stage production Dockerfile
- Separate production and mock-service image targets
- Non-root UID and GID
- Read-only root filesystems
- Ephemeral writable temporary storage
- Dropped Linux capabilities
- Prevention of privilege escalation
- CPU, memory, and PID limits
- Bounded container log rotation
- Internal Docker Compose service networking
- Liveness and readiness health checks
- Automated dependency-failure and recovery drill

#### Continuous Integration and Supply Chain

- Python quality and package CI workflow
- Hardened container CI workflow
- Buildx build caching
- Failure-diagnostic artifact collection
- Dependabot coverage for uv, GitHub Actions, and Docker
- Tag-driven release automation
- CycloneDX SBOM generation
- SHA-256 release checksums
- GitHub artifact provenance attestations
- Automated GitHub release publication

### Release Assets

The `v0.1.0` GitHub release includes:

- Python wheel
- Python source distribution
- Production Linux AMD64 container archive
- Mock model-service Linux AMD64 container archive
- CycloneDX dependency SBOM
- SHA-256 checksum manifest

### Known Limitations

- Prompt generation is non-streaming.
- The included model service is deterministic and intended for testing.
- Container archives currently target Linux AMD64.
- No container registry publication is included.
- GPU passthrough and NVIDIA runtime support are planned for later phases.
- Production authentication, authorization, TLS, secret management, and observability remain future work.