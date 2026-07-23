# Phase 10 — Frontend CI verification

## Baseline inspection

This branch begins at the latest locally available integrated Phase 10 administrative-web baseline.
The repository has one isolated JavaScript project, `apps/web/package.json`. Its README, the root
README, and the Makefile document **npm** as the package manager. At baseline, the repository has
no `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`; the existing backend workflow is Python-only.

The inspected frontend configuration consists of `next.config.ts`, `tsconfig.json`,
`vitest.config.ts`, and `playwright.config.ts`. The web package declares the direct runtime and
development dependencies used by the application, tests, and tooling. This work does not add
learner-facing functionality or begin Phase 11.

## Implementation plan

1. Generate the authoritative lockfile with `npm install` using the official npm registry and
   commit it at `apps/web/package-lock.json`. This location is chosen because `apps/web` is the
   only JavaScript package and is intentionally an isolated npm project; no root `package.json`
   exists.
2. Audit direct imports, scripts, and peer compatibility; correct only missing or incompatible
   direct declarations and normalize the format-check script.
3. Add a separate GitHub Actions frontend workflow using Node.js 22 LTS, `npm ci`, and repository
   scripts for formatting, linting, typechecking, unit/component testing, production build, and
   deterministic mocked browser smoke testing. Keep existing backend CI unchanged.
4. Run each frozen-install frontend check locally when the registry permits and address only
   concrete Phase 10 verification failures. Configure safe, non-secret public CI environment
   values.
5. Record exact CI commands, browser-test status, and only remaining infrastructure-dependent
   deferred checks in the project documentation.

## Dependency audit and current result

The direct-import audit found direct declarations for Next.js, React and React DOM, TypeScript and
the Node/React type packages, TanStack Query, React Hook Form, `@hookform/resolvers`, Zod,
Vitest, Testing Library, jsdom, Playwright, ESLint/`eslint-config-next`, and Prettier. Tailwind is
declared for the existing stylesheet pipeline; no unimported UI library, Markdown renderer, or
sanitization package was added. The declared React 19, Next 15, ESLint 9, and matching Next ESLint
configuration versions are intentionally aligned.

The package scripts now provide the authoritative CI commands: `format:check`, `lint`,
`typecheck`, `test`, `build`, and `e2e:mock`. The initial `npm install` attempt on 2026-07-23 still
received HTTP 403 for `@hookform/resolvers`; therefore this environment cannot generate the
required npm-authored lockfile, `npm ci` correctly refuses to run without it, and no frontend
runtime command is marked passed here. The workflow is ready to run those exact commands once an
approved environment creates and commits that lockfile.
