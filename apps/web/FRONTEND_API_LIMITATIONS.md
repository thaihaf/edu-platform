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
