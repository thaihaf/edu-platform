# Web application placeholder

The learner and administration web clients are intentionally deferred to the UI
phases. This directory reserves the monorepo boundary so the FastAPI backend does
not depend on a frontend framework.

## Phase 10C administration boundary

Course and question generation use the implemented FastAPI asynchronous job contracts. Course
editing/review/publication and Phase 9 evaluation management are intentionally unavailable until
the backend publishes typed contracts; see `FRONTEND_API_LIMITATIONS.md`. This keeps published
artifacts immutable in the browser and preserves FastAPI as the business-policy boundary. The
course-editor design treats every block as safe structured text and requires visible lock,
confidence, attribution, citation, and validation information when the backend provides it.
Question review will require API-backed revisions and evidence; evaluation management will require
API-backed datasets, policies, baselines, compatibility checks, and gate results.
