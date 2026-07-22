# Phase 2 — Domain and Data implementation notes

## Scope

This phase adds the project, source, course, course-version, and audit-event domain model; persistence adapters; migrations; and CRUD HTTP APIs. It deliberately does not implement ingestion, crawling, research, generation, or any Phase 3 work.

## Decisions

- Domain entities and repository protocols use only Python standard-library types and do not import SQLAlchemy or vendor SDKs.
- SQLAlchemy 2 asynchronous adapters implement the repository protocols, with Alembic owning production schema changes.
- Source snapshots are append-only. Repository APIs expose creation and retrieval only; no update operation exists.
- A published course version is immutable. Editing content is allowed only while a version is a draft; publication records a state transition and audit event.
- Infrastructure-dependent integration tests remain marked for PostgreSQL/Docker execution. Isolated repository tests use in-memory SQLite without adding SQLite-specific production behavior.

## Deferred verification

Docker-dependent verification is recorded in [the deferred verification register](../deferred-verification.md) and has not been claimed as passed.
