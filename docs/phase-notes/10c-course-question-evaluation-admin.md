# Phase 10C — Course, question, and evaluation administration

## Baseline verification

The latest available local integration baseline was `work` at `cbc44fd`, containing merged
Phase 10A and 10B. It has `apps/web` as a strict TypeScript Next.js App Router admin application,
a shared shell with workspace/project controls, typed trace-aware API transport with idempotency
keys, safe text rendering, a React Hook Form/Zod project wizard, and TanStack Query. Phase 10B
adds API-backed project/source/research/claim administration, bounded job polling and explicit
unavailable states for undocumented reads.

## Implementation plan

1. Extend the existing typed transport only for implemented Phase 7/8 generation-job contracts;
   model all missing course, question-bank, and evaluation contracts as explicit unavailable UI.
2. Add reusable, accessible Phase 10C primitives for confidence/origin/quality status, immutable
   version controls, JSON validation, citations, protected blocks, and safe structured blocks.
3. Add course and question generation forms and polling job detail routes using React Hook Form,
   Zod, TanStack Query, idempotency keys, targeted cache invalidation, and no fabricated results.
4. Add every requested course, question-bank, and evaluation route. Routes without a backend
   contract display the typed unavailable state and document the specific API gap.
5. Add deterministic unit coverage for the reusable safety/status primitives and mocked API
   feature coverage, then update UI/security/accessibility/API-limit/deferred-verification docs.

## Verified API limits

The current FastAPI application implements course-generation start/read/events and
question-generation start/read/events. It does not expose course lists, course/version/module/
lesson/editor/validation/publication reads or mutations; question bank/review/version/revision/
duplicate-cluster reads or mutations; or any Phase 9 evaluation, dataset, policy, or baseline API
routes. This phase therefore provides supported job workflows and safe unavailable states for the
remaining required administration screens rather than inventing response shapes or client-side
publication policy.
