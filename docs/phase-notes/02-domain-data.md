# Phase 2 — Domain and data implementation plan

## Plan
1. Define framework-independent UUID domain entities, lifecycle enums, immutable snapshots, and append-only audit events.
2. Add repository ports and a unit-of-work boundary; implement use cases that persist each mutation and audit event atomically.
3. Add async SQLAlchemy mappings, repository adapters, and an Alembic migration for the domain-agnostic schema.
4. Expose the specified `/api/v1` CRUD and course-version lifecycle endpoints with the Phase 1 trace/error contract.
5. Add unit/API/persistence-ready tests and document deferred Docker/PostgreSQL verification.

## Scope boundaries
No ingestion, object storage, crawling, search, AI generation, embeddings, or Phase 3 capabilities are included.
