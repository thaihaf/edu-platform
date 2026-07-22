# Phase 5 — Research engine implementation plan

## Plan
1. Replace the earlier queued-state placeholder with complete vendor-neutral contracts for the
   lifecycle, serializable ID-only state, brief, query, selection, observation, coverage, gap,
   result, events, prompts, and repositories.
2. Build a deterministic in-memory node runner for application tests.  It invokes typed model operations and preserves the orchestration boundaries for the
   Phase 3/4 adapters, checkpoints after every meaningful node, prevents duplicate
   side effects, and uses deterministic policy as the final budget/follow-up authority.
3. Keep the production LangGraph adapter optional and behind `ResearchWorkflow`; model-provider
   output stays in infrastructure.  The API only queues jobs and exposes lifecycle/artifact reads.
4. Extend Phase 5 persistence metadata and its migration without adding Phase 6 claims or
   evidence-link tables.  Persist job lifecycle/idempotency, checkpoints, artifacts,
   observations, gaps, source/query linkage and events.
5. Add focused lifecycle, policy, orchestration, checkpoint, extraction and injection-regression
   tests; document prompts, cancellation, retention, bounded follow-up, and unavailable live
   infrastructure verification.

## Scope boundary
This phase stores candidate observations only. It does not create final claims/evidence links, skills, courses, lessons, or questions.
