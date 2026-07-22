# Changelog

All notable changes to this project are documented in this file.

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
