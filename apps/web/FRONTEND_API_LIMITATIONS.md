# Phase 10C frontend API limitations

The typed client consumes only endpoints implemented by `apps/api/app/main.py`: start/read/events
for course generation and question generation. The job forms send idempotency keys and navigate
only using IDs returned by FastAPI.

No FastAPI route currently provides paginated course/question-bank lists, course modules/lessons/
blocks/citations/validation/publication, question review/revisions/duplicate clusters, or Phase 9
evaluation runs, datasets, policies, and baselines. Corresponding UI pages render `Unavailable`
with their required endpoint. This prevents fabricated records and keeps FastAPI as the policy
boundary. Mock fixtures may be used only in test/development mode and must never enter a
production route.

## Phase 11 learner boundary

No live learner endpoints are implemented by the current FastAPI baseline. The `/learn` route group
therefore uses a typed, deterministic learner-safe fixture only under `NEXT_PUBLIC_MOCK_MODE=true`.
Outside that development/test boundary it renders access-required UI rather than requesting or
inventing learner records. Live learner APIs must provide published-only filtering, ownership checks,
version pinning, idempotent mutations, and learner-safe serializers before this fixture is replaced.
