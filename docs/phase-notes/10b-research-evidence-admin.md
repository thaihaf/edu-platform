# Phase 10B — Research and evidence administration

## Phase 10A verification

The current `apps/web` baseline is a strict-TypeScript Next.js App Router application with a
shared admin shell, workspace/project selectors and navigation. It already provides a typed
transport that emits trace and idempotency headers, renders structured API errors with trace IDs,
uses TanStack Query plus React Hook Form/Zod, safely renders untrusted text as text, retains a
project-wizard draft, and documents the stack in ADR 0010 and the Phase 10 notes.

## Implementation plan

1. Extend the existing typed transport with schemas only for documented FastAPI contracts and
   expose reusable query/mutation hooks with bounded polling and targeted invalidation.
2. Add reusable accessible status, table, action-confirmation, API-state, quality, confidence,
   origin, tree, and severity components; unimplemented contracts must render a typed
   availability notice rather than fabricated data.
3. Add the Phase 10B project-scoped routes for sources, research, claims, reported questions,
   skills, clusters, and knowledge gaps, and the supported source/research/claim actions.
4. Update dashboard and project views to explain aggregate/list limitations without N+1 fetches;
   preserve Phase 10C course/question/evaluation placeholders without expanding them.
5. Add focused component and MSW-ready feature tests, update UI/security/accessibility/API
   limitation documentation, then run every available check without claiming unavailable tools.

## Verified API limits at implementation start

The backend documents individual project, source, research-job, ingestion-job, claim, evidence,
contradiction, and review-decision reads plus text/URL source ingestion, research lifecycle, and
claim review. It does **not** currently document project-list, research-job-list, search/fetch,
source-cluster, reported-question, skill/prerequisite, or knowledge-gap read contracts. Phase
10B surfaces these as typed not-available states and recommends narrow aggregate/list reads;
it does not mock them in production or add browser-side domain policy.
