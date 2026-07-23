# Phase 10 — Administrative web implementation plan

## Baseline verification

Phase 9 is present on the latest available integration baseline (`work`): its implementation
scopes evaluation idempotency by project, registers deterministic metrics by name/version,
rejects incompatible metrics, keeps published datasets immutable, appends results and decisions,
and compares compatible metric versions. The focused Phase 9 tests and CI-safe CLI commands
cover those policies without requiring DeepEval.

## Plan

1. Add the admin-web architecture ADR and scaffold `apps/web` as a strict TypeScript Next.js
   App Router application, keeping all policy decisions in the FastAPI API.
2. Build the typed HTTP client, authentication boundary, query provider, shared accessible
   primitives, mock adapter, and environment configuration.
3. Implement the responsive shell and bounded-context routes, with API-driven lists, detail
   panels, mutation forms, immutable-version affordances, error/empty/loading states, and
   a static deferred-verification manifest.
4. Add focused unit, feature, and mocked browser smoke specifications; wire web commands and CI
   without changing backend workflows.
5. Update UI, setup, security, accessibility, mocking, changelog, and deferred-verification
   documentation; run all available checks and record environment-limited frontend checks.

## Scope boundary

This phase is an administrator studio only. It does not add learner experiences, progress,
adaptation, spaced repetition, learner analytics, or voice interviewing.
