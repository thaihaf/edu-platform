# Phase 10 administrative web

This is the strict-TypeScript Next.js App Router administrator studio. It is not a learner
application. Use npm only: after `package-lock.json` is generated and committed in an approved
registry environment, install with `npm ci` from this directory and run `npm run lint`,
`npm run typecheck`, `npm run test`, `npm run build`, and `npm run e2e:mock`.

The initial verification attempt on 2026-07-23 could not create the lockfile because npm received
HTTP 403 while fetching `@hookform/resolvers` from `https://registry.npmjs.org`. No registry
mirror, credentials, TLS bypass, or dependency substitution was used. See
`../../docs/phase-notes/10-frontend-verification.md` for the plan and
`../../docs/deferred-verification.md` for the remaining deferred checks.

## Phase 10C administration boundary

Course and question generation use the implemented FastAPI asynchronous job contracts. Course
editing/review/publication and Phase 9 evaluation management are intentionally unavailable until
the backend publishes typed contracts; see `FRONTEND_API_LIMITATIONS.md`. This keeps published
artifacts immutable in the browser and preserves FastAPI as the business-policy boundary. The
course-editor design treats every block as safe structured text and requires visible lock,
confidence, attribution, citation, and validation information when the backend provides it.
Question review will require API-backed revisions and evidence; evaluation management will require
API-backed datasets, policies, baselines, compatibility checks, and gate results.
