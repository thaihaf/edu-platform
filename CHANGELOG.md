# Changelog

## Phase 8

- Add framework-neutral validated assessment-question contracts, deterministic quality gates,
  question-bank drafts/publication, review history, and an asynchronous generation-job API boundary.
- Complete project-scoped idempotency, meaningful non-choice answer/rubric validation, approval revocation, direct reported-evidence citations, independent-solver isolation, and ambiguity publication gates.

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

## Phase 6

- Added deterministic evidence and knowledge graph foundations, claim fingerprints, confidence policy, immutable evidence links, review decisions and relational migration groundwork.

## Phase 7

- Added deterministic cited course draft generation, validation, versioning, and rollback foundations.

## Phase 9 — Evaluation

- Added provider-neutral deterministic evaluation, metric registry, quality gates, golden fixtures, baseline comparison, optional DeepEval boundary, and CI-safe smoke commands.

## Phase 10 — Admin web

- Added the Next.js administrative research and course studio scaffold, typed API transport,
  authentication boundary, accessible application shell, bounded-context routes, project wizard,
  common error/loading/empty/status primitives, and deterministic test specifications.
- Documented the frontend architecture, API/source-of-truth boundary, security/accessibility
  approach, environment configuration, mock strategy, and deferred live verification.

## Phase 10B — Research and evidence administration

- Added project-scoped Phase 10B routes, typed FastAPI transport models, source ingestion,
  bounded research-job polling/actions, and claim-review UI with structured API errors.
- Added explicit non-mocking availability states for missing paginated administrative API reads.
- Documented API, security, accessibility, mock-fixture, and verification limits for this phase.

## Phase 10C — Course, question, and evaluation administration

- Added typed, idempotent course and question generation forms and terminal-aware job polling.
- Added the Phase 10C route inventory and safe API-unavailable states for course editor/version,
  question review/version, evaluation, golden dataset, quality-gate policy, and baseline contracts
  that the current FastAPI application does not yet expose.
- Added reusable textual confidence/origin/gate/regression, immutable-version, protected-content,
  citation, and JSON-safety admin primitives plus Phase 10C API-limit and UX documentation.

## Phase 10 — Frontend verification

- Added the Phase 10 frontend CI workflow design: Node.js 22, frozen npm installation, formatting,
  lint, strict typecheck, unit/component tests, production build, and a separate mocked Chromium
  smoke job with failure artifacts.
- Normalized the frontend format-check and ESLint commands and configured Playwright failure traces
  and screenshots for the mocked smoke suite.
- Committed the npm-generated `apps/web/package-lock.json` and updated frontend CI to run every
  frontend check from that lockfile with `npm --prefix apps/web ci`.
- Verified lockfile metadata matches `apps/web/package.json`. Local install-dependent frontend
  checks remain unclaimed because the environment returns HTTP 403 for locked npm tarball downloads.
