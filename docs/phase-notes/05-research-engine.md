# Phase 5 — Research engine implementation plan

## Plan
1. Define vendor-neutral research lifecycle, typed serializable state, brief, query, selection, observation, coverage, gap, result, and port contracts.
2. Add deterministic in-memory repositories/model/workflow runner plus an optional LangGraph adapter behind the workflow port.
3. Implement research use cases, budget/idempotency/cancellation/checkpoint policy, prompt-injection detection, and asynchronous API job-control endpoints.
4. Add Phase 5 persistence metadata and migration without Phase 6 evidence/claim tables.
5. Add focused tests and document workflow, security, deferred infrastructure checks, and architectural decisions.

## Scope boundary
This phase stores candidate observations only. It does not create final claims/evidence links, skills, courses, lessons, or questions.
