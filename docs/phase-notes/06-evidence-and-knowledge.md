# Phase 6 — Evidence and knowledge implementation plan

## Plan
1. Add framework-independent evidence, claim, review, reported-question, skill-graph, and gap domain contracts with deterministic fingerprints, immutable links, lifecycle guards, and graph-cycle validation.
2. Add application policies for deterministic normalization, source-independence clustering, relation classification, confidence assessment, verification, and evidence-build idempotency; use only repository/model ports.
3. Provide deterministic in-memory repositories/adapters and expose Phase 6 read, build, review, graph, and gap API operations without scoring in routes.
4. Add relational SQLAlchemy metadata and an Alembic migration for Phase 6 entities, constraints, indexes, and append-only/immutable persistence contracts.
5. Add focused unit/API/migration-oriented tests and document policy decisions, security controls, limitations, ADRs, and deferred infrastructure verification.

## Scope boundary
Phase 6 converts Phase 5 candidate observations into reviewable evidence and knowledge artifacts. It does not generate curricula, lessons, assessments, distractors, learner progress, or learner UI.
