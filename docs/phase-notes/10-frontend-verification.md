# Phase 10 — Frontend verification and stabilization

## Baseline and scope

This verification branch starts from the latest locally available integrated Phase 10 baseline.
It is limited to the Phase 10 administrator web in `apps/web`; it does not add learner-facing
features or begin Phase 11.

## Verification plan

1. Use npm because the repository documents npm for the web application and contains no
   competing JavaScript lockfile. Create and commit the npm lockfile only after a successful
   installation from the configured registry.
2. Compare every direct web import and script with `apps/web/package.json`, then run the frozen
   npm installation once the lockfile exists.
3. Run format checking, linting, strict TypeScript checking, Vitest, the production build, and
   the mocked Playwright flow. Correct only concrete dependency, contract, security, accessibility,
   or frontend-runtime defects that those checks reveal.
4. Compare the typed transport and feature requests with the FastAPI route declarations and
   request/response schemas. Retain explicit unavailable states for undocumented contracts.
5. Run the required backend regression commands and `git diff --check`; document exact results
   and retain only genuinely infrastructure-dependent live checks as deferred.

## Initial package-manager status

There was no `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock` at branch creation. The root
README and Makefile document npm commands for `apps/web`, so npm is the sole package manager for
this task. No alternate lockfile will be created.

## 2026-07-23 verification repair

The installed Next 15 / `eslint-config-next` 15 configuration exposes the Next rules as a
legacy shareable config rather than an ESM flat-config array. The ESLint flat config now adapts
`next/core-web-vitals` with `FlatCompat`, preserving the complete Next Core Web Vitals rule set.
It does not disable or replace any Next.js rules.

The Phase 10C regression indicator now receives its typed optional `compatible` prop and keeps
its explicit incompatible-metric-version text. Both generation-job detail views now distinguish
loading, request-error, and absent-job states before binding a typed job value, so job properties
are never read from an absent query result. The component test covers the incompatible metric
state.

Vitest now uses Vite's automatic JSX runtime and excludes `tests/e2e/**`; Playwright continues
to own that directory through `playwright.config.ts`. The typed API-client test normalizes the
mock request headers with `new Headers(...)` before reading `Idempotency-Key`.

### Actual local results

- `npm run format:check` passed.
- `npm run lint` and `npm run typecheck` could not complete because the local `node_modules`
  tree was incomplete after the registry denied locked package tarball downloads with HTTP 403.
- `npm run test`, `npm run build`, and `npm run e2e:mock` consequently could not start because
  their executables were absent. The Playwright startup configuration was not weakened.
- `make check` passed its Ruff format, Ruff lint, and mypy stages; `pytest -m "not integration
  and not e2e"` passed (51 tests); `make eval-smoke`, `make eval-golden`, and `git diff --check`
  passed.
