# Phase 7 — Course generation implementation plan

## Plan
1. Add framework-independent curriculum, lesson, citation, confidence, generation-job, and review contracts with lifecycle and immutability guards.
2. Implement deterministic evidence selection, prerequisite-aware planning, fake model adapters, draft validation, content locking, version copying/rollback, diffs, and idempotent in-memory generation orchestration.
3. Add provider-neutral prompt registry, persistence metadata/migration, and API operations that delegate to the application service.
4. Document the policies, ADRs, and deferred infrastructure checks; add focused unit and API coverage without generating Phase 8 questions.

## Scope boundary
Phase 7 creates cited, reviewable **draft** courses from approved Phase 6 knowledge. It does
not generate assessment questions, learner progress, adaptive behavior, flashcards, or learner UI.
