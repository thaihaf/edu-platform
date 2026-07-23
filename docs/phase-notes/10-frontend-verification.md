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
