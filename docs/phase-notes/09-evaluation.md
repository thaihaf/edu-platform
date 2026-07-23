# Phase 9 — Evaluation implementation plan

## Plan

1. Define framework-independent evaluation contracts, versioned dataset/policy entities,
   metric registry, provider/JudgeModel ports, run lifecycle, and typed error codes.
2. Implement deterministic, provenance-aware metrics and an in-memory repository/runner with
   idempotent starts, resumable results, aggregates, gates, baseline comparisons, events, and
   review sampling; keep model evaluation optional behind adapters.
3. Add a DeepEval adapter with an optional import and typed, sanitized boundary, plus JSONL
   golden datasets and CI-safe validation/smoke commands.
4. Add persistence metadata/migration and API queue/read controls without moving metric logic
   into routes.
5. Add focused deterministic tests and document policies, security boundaries, deferred live
   infrastructure verification, and evaluation API/data-model changes.

## Scope boundary

This phase evaluates existing research, evidence, course, question, retrieval, and model-output
artifacts. It does not implement learner progress, adaptive learning, spaced repetition, learner
analytics, or a learner/admin UI.
