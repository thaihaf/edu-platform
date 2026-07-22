# Phase 3 — Source ingestion implementation plan

## Plan

1. Add vendor-independent ingestion domain types, state-machine rules, structured
   document/chunk models, and ports for storage, parsing, embeddings, chunks, jobs,
   events, and future URL resolution.
2. Implement deterministic in-memory adapters, secure input/URL validation, a
   plain-text parser, a mocked-testable Docling boundary, structure-aware chunking,
   and deterministic embeddings.
3. Orchestrate synchronous-in-process ingestion behind asynchronous `202` job
   semantics with idempotency, stage progress, compensation, and provenance-safe
   duplicate handling; expose the Phase 3 API routes.
4. Add SQLAlchemy metadata and an Alembic migration for jobs/chunks and document
   PostgreSQL/pgvector integration boundaries.
5. Add unit and API tests, update operational/security/API documentation and
   deferred verification, then run all checks available without Docker.

## Scope boundaries

URLs are validated and registered only: this phase never resolves DNS, fetches,
crawls, follows redirects, searches, or invokes research/generation workflows.
Real MinIO, PostgreSQL/pgvector, Docling, Celery/Redis worker, and API-to-worker
execution remain integration verification.
