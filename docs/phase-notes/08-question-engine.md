# Phase 8 — Question engine implementation plan

## Plan

1. Add framework-neutral assessment entities, state machines, validation records, and
   provider ports for generation, independent solving, review, similarity, and disabled
   execution sandboxes.
2. Implement deterministic question policies and orchestration: idempotent jobs,
   blueprint validation, reported-question materialization, quality gates, review history,
   duplicate clustering, and immutable question-bank version cloning/publication.
3. Provide in-memory adapters and asynchronous API queue boundaries so unit/API tests do
   not require model, worker, database, or sandbox infrastructure.
4. Add PostgreSQL-compatible Alembic metadata/migration, documentation, ADRs, and focused
   tests for provenance, gates, retries, independent solving, and draft independence.

## Scope boundary

This phase implements assessment authoring and review only. It does not implement learner
progress, adaptive learning, spaced repetition, learner analytics/UI, proctoring, or Phase 9
evaluation dashboards.
