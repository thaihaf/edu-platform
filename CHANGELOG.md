# Changelog

All notable changes to this project are documented in this file.

## [0.3.0] - 2026-07-22

### Added
- Vendor-neutral ingestion jobs, structured document/chunk domain models, ports,
  deterministic in-memory adapters, plain-text parsing, chunking, embeddings, and
  URL-registration validation.
- Ingestion job/chunk persistence metadata and Phase 3 Alembic migration.

## [0.1.0] - 2026-07-22

### Added

- Phase 1 modular-monolith foundation with FastAPI, Celery, shared packages, and a
  web application placeholder.
- Local Docker Compose stack for PostgreSQL with pgvector, Redis, MinIO, and
  SearXNG.
- Dependency-aware health endpoints, JSON structured logging, and trace ID
  propagation.
- Ruff, mypy, pytest, and GitHub Actions continuous-integration configuration.

## [0.2.0] - 2026-07-22

### Added
- Phase 2 domain entities, lifecycle rules, repository ports, use cases, SQLAlchemy metadata, and Alembic schema migration.
- `/api/v1` workspace, project, source/snapshot, and course-version foundation endpoints with trace-aware errors.

## Phase 4 — Search and crawling
- Added provider-neutral web search/fetch contracts, deterministic SearXNG mapping and safe mocked adapters.
- Added URL canonicalization, DNS-based SSRF checks, redirect validation, robots fail-closed policy, HTML normalization, RRF fusion, and disabled browser boundary.

## Phase 5
- Added provider-neutral, resumable research-job contracts, typed checkpoint state, budget and lifecycle controls, and asynchronous job-control API surface.
- Added deterministic node-runner checkpoints, immutable artifact persistence, idempotent finalization, versioned structured prompt descriptors, and injection-safe source delimiters for unit testing.
- Declared the optional-at-runtime LangGraph workflow adapter and documented deferred live orchestration verification.
