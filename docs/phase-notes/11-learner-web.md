# Phase 11 — Learner web implementation plan

## Baseline

This branch starts at the latest locally available integrated baseline (`work`, commit
`3f6c83f`) because this checkout has no `main` ref or remote. The graph contains merged
Phases 1–10 and the repaired Phase 10 frontend baseline. Format, lint, typecheck, unit
and production-build checks passed before changes. Mocked Playwright could not launch:
the pinned Chromium executable is absent and the configured CDN returned HTTP 403 when
installation was attempted. Backend checks, pytest, eval smoke, eval golden, and diff
checking passed without Docker.

## Plan

1. Add a learner route group and separate learner-only shell, typed learner contracts,
   deterministic development/test fixtures, and user/version-scoped query keys. Keep admin
   routes and caches independent.
2. Add learner-safe content, citation, progress, assessment, flashcard, interview, and
   skill-summary components. Render blocks as text/structured React only; sanitize markdown
   and external links; never place answer keys in pre-submission client contracts.
3. Add the narrow in-memory Phase 11 learning service and `/api/v1/learner` endpoints with
   published-only filtering, version-pinned progress/sessions, ownership checks, idempotent
   answers, and learner-safe serializers.
4. Implement every required learner route with explicit unavailable states outside mock mode,
   then add unit/API and mocked-browser coverage for course, practice, exam, flashcard, and
   interview flows.
5. Document learner policies, data/API additions, security/privacy/accessibility limits,
   deferred live checks, and architectural decisions; run all available checks.

## Scope boundary

This phase delivers deterministic learner consumption only. It excludes adaptive curricula,
advanced spaced repetition, voice interviews, proctoring, payments, subscriptions, marketplace,
social features, mobile apps, and live infrastructure hardening.

## Delivered implementation

The existing Next.js application now has the `(learner)` route group and all required `/learn` URLs.
Its learner-only navigation is isolated from the Phase 10 admin shell. In explicit mock mode it
renders deterministic published course/version fixtures, a structured non-executable lesson reader,
safe citations, lesson completion UI, practice/exam disclosure behavior, flashcards, text interview,
and explainable skill recommendation UI. In every other mode it shows access-required UI rather
than silently granting a learner identity or fabricating progress.

The current FastAPI baseline has no learner contracts, persistence, migrations, or real identity
integration. Accordingly, this frontend phase does not claim live progress, scoring, session
persistence, cross-user authorization, or API-to-browser integration. Those backend gaps are
recorded in `apps/web/FRONTEND_API_LIMITATIONS.md` and deferred verification.
