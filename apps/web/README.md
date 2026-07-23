# Phase 10 administrative web

This is the strict-TypeScript Next.js App Router administrator studio. It is not a learner
application. It is an isolated npm project: its sole authoritative lockfile is
`apps/web/package-lock.json`. It is an npm lockfile (format version 3) whose root dependency
metadata matches `package.json`; use `npm --prefix apps/web ci` for all local and CI installations.
Do not use pnpm, Yarn, an alternate registry, or a manually written lockfile.

Frontend CI (`.github/workflows/frontend.yml`) uses Node.js 22 and safe mock-only public values. It
runs `npm --prefix apps/web run format:check`, `npm --prefix apps/web run lint`,
`npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and
`npm --prefix apps/web run build`; a separate Chromium job runs
`npm --prefix apps/web exec -- playwright install --with-deps chromium` and
`npm --prefix apps/web run e2e:mock`.
The smoke suite starts the production build and uses `NEXT_PUBLIC_MOCK_MODE=true`, so it neither
requires Docker nor a live backend. Browser reports, screenshots, and traces are uploaded when the
browser job fails.

See `../../docs/phase-notes/10-frontend-ci-verification.md` for verification status and
`../../docs/deferred-verification.md` for remaining live-infrastructure checks.

## Phase 10C administration boundary

Course and question generation use the implemented FastAPI asynchronous job contracts. Course
editing/review/publication and Phase 9 evaluation management are intentionally unavailable until
the backend publishes typed contracts; see `FRONTEND_API_LIMITATIONS.md`. This keeps published
artifacts immutable in the browser and preserves FastAPI as the business-policy boundary. The
course-editor design treats every block as safe structured text and requires visible lock,
confidence, attribution, citation, and validation information when the backend provides it.
Question review will require API-backed revisions and evidence; evaluation management will require
API-backed datasets, policies, baselines, compatibility checks, and gate results.
