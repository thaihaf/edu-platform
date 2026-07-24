# Deferred verification

Docker is unavailable in this execution environment, so no Docker command was run or installed.

| Check/category                                                                | Reason                                                       | Type          | Later execution                                         |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------- | ------------------------------------------------------- |
| `docker compose config` runtime validation                                    | Docker unavailable                                           | environmental | `docker compose config` in a Docker-enabled runner      |
| PostgreSQL repository integration tests (`integration`)                       | no PostgreSQL service                                        | environmental | `pytest -m integration` against Compose PostgreSQL      |
| Alembic upgrade/downgrade on PostgreSQL                                       | no PostgreSQL service                                        | environmental | `alembic upgrade head && alembic downgrade base`        |
| Redis readiness and Celery broker ping                                        | Docker unavailable                                           | environmental | run Compose then health/worker checks                   |
| MinIO and SearXNG connectivity                                                | Docker unavailable                                           | environmental | run Compose service probes                              |
| MinIO source-object upload integration                                        | Docker unavailable                                           | environmental | exercise S3-compatible adapter against Compose MinIO    |
| PostgreSQL source-chunk persistence and pgvector extension/dimension behavior | no PostgreSQL service                                        | environmental | run `pytest -m integration` against pgvector PostgreSQL |
| Docling PDF/DOCX real-file conversion                                         | optional Docling dependency/integration fixtures unavailable | environmental | install `.[docling]` and run parser integration tests   |
| Celery/Redis ingestion execution and API-to-worker end-to-end ingestion       | Docker unavailable                                           | environmental | run Compose worker and e2e suite                        |

Offline PostgreSQL Alembic SQL generation and static Compose YAML parsing remain local checks.
| SearXNG live search | Docker unavailable | integration | run mocked and live provider suite against Compose SearXNG |
| Crawl4AI live page extraction | optional browser/runtime unavailable | integration | install `.[crawl]` and run public-page fixtures |
| Real DNS/redirect SSRF controls | external network intentionally not used | e2e | execute controlled DNS rebinding and redirect test environment |
| PostgreSQL search/fetch persistence | no PostgreSQL service | integration | run migration/repository suite against Compose PostgreSQL |
| Redis/Celery search/fetch execution | Docker unavailable | integration | run worker retries against Redis |
| MinIO snapshot persistence | Docker unavailable | integration | run snapshot object-storage suite |
| Browser-provider execution | disabled by default; runtime unavailable | e2e | explicitly enable against public allowed fixture |
| External network policy verification | external crawling prohibited in this environment | e2e | run approved public-network verification |
| Live LangGraph checkpoint execution | LangGraph/package runtime and worker infrastructure unavailable | integration | install project dependencies and run a LangGraph worker/checkpointer suite |
| PostgreSQL research checkpoint persistence | no PostgreSQL service | integration | run research repository tests against Compose PostgreSQL |
| Redis/Celery research execution and API-to-worker flow | Docker unavailable | e2e | run worker and API end-to-end suite with Redis/Celery |
| Live SearXNG/Crawl4AI orchestration | Docker/browser runtime unavailable | integration | run approved provider orchestration fixtures |
| Real structured-output model, token and cost accounting | no model credentials/provider configured | integration | configure provider then run model contract suite |
| API-to-worker research execution | API deliberately only queues work; no worker/Redis runtime available | e2e | run worker with Redis and invoke `POST /api/v1/projects/{id}/research-jobs` |
| Live PostgreSQL Phase 6 evidence persistence and database constraints | no PostgreSQL service | integration | run Phase 6 repository/migration suite against PostgreSQL |
| Celery evidence-build execution and API-to-worker flow | Docker unavailable | e2e | run Compose API, worker and Redis evidence-build suite |
| Large-corpus source clustering and optional Neo4j adapter | infrastructure/runtime unavailable | integration | run corpus and graph-adapter benchmarks |
| Real model-assisted normalization | no model credentials/provider configured | integration | run structured model contract suite |
| Live PostgreSQL Phase 7 course persistence and immutable constraints | no PostgreSQL service | integration | run Phase 7 repository/migration suite against PostgreSQL |
| Celery course-generation execution and API-to-worker generation | Docker unavailable | e2e | run Compose API, worker and Redis suite |
| Real structured course/lesson model calls, token and cost accounting | no model credentials/provider configured | integration | configure provider and run model contracts |
| Large-course generation | worker/database runtime unavailable | integration | run benchmark fixture with PostgreSQL and worker |
| Rendering-sanitization integration | web rendering runtime unavailable | integration | run API-to-renderer sanitization suite |
| Live PostgreSQL Phase 8 question persistence and constraints | no PostgreSQL service | integration | run question repository and migration suite against PostgreSQL |
| Redis/Celery question generation and API-to-worker execution | Docker unavailable | e2e | run Compose API, worker, and Redis question suite |
| Real-model generation, independent solving (with sanitized requests), grounding and ambiguity review | no model credentials/provider configured | integration | run provider contract suite |
| Code/SQL sandbox and large-bank duplicate detection | safe sandbox/runtime unavailable | integration | run isolated sandbox and benchmark suites |
| Token/cost accounting | no provider runtime | integration | run model accounting fixture |
| Live PostgreSQL evaluation persistence and immutable constraints | no PostgreSQL service | integration | run Phase 9 migration/repository suite |
| Redis/Celery evaluation dispatch and API-to-worker flow | Docker unavailable | e2e | run Compose evaluation worker suite |
| Real DeepEval runtime and external judge models | optional dependency/credentials unavailable | integration | configure providers and run contract suite |
| Large-dataset performance and token/cost accounting | worker/model infrastructure unavailable | integration | run benchmark with configured provider |

## Phase 10 administrative web

| Check                              | Reason deferred                                                                                                                                         | Category    | Command / required infrastructure                                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Frozen frontend install and checks | The committed npm v3 lockfile matches `package.json`, but this environment receives HTTP 403 for locked package tarballs from the official npm registry | build / CI  | Run `npm --prefix apps/web ci` in GitHub Actions or an approved registry environment, then run all frontend scripts |
| Live FastAPI integration           | no persistent API process/data fixtures available                                                                                                       | integration | run API and `NEXT_PUBLIC_MOCK_MODE=false npm run dev`                                                               |
| Production authentication adapter  | identity provider/session host not selected                                                                                                             | integration | configure host bearer/session adapter and authorization contract tests                                              |
| Live file upload                   | object storage and upload endpoint unavailable                                                                                                          | integration | run source-file ingestion against configured object storage                                                         |
| Live SSE/event streaming           | worker/event broker unavailable                                                                                                                         | integration | run research/generation jobs with worker and SSE endpoint                                                           |
| Mocked browser smoke               | Playwright dependencies cannot be installed without package registry                                                                                    | e2e         | `make web-e2e-mock` after `make web-install`                                                                        |
| Deployment production build        | frontend dependencies unavailable locally                                                                                                               | build       | `make web-build` in CI/deployment environment                                                                       |

| Phase 10B paginated dashboard and administration lists | documented FastAPI list/aggregate contracts are absent | API integration | add narrow read-only contracts for projects, jobs, search/fetch, clusters, questions, skills, and gaps; then add MSW/browser coverage |
| Phase 10B component, MSW, and Playwright coverage | frontend dependencies unavailable locally | frontend tests | run `npm --prefix apps/web run test` and `npm --prefix apps/web run e2e:mock` after installing dependencies |

## Phase 10C frontend verification and API limitations

| Check/category                           | Reason                                                                                                                        | Type        | Later execution                                                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------- |
| `npm --prefix apps/web ci`               | Official-registry tarball downloads return HTTP 403 in this environment; the committed lockfile itself matches `package.json` | dependency  | run in an approved registry environment                              |
| `npm --prefix apps/web run format:check` | frontend dependencies cannot be installed from the official registry in this environment                                      | frontend    | run after successful `npm --prefix apps/web ci`                      |
| `npm --prefix apps/web run lint`         | frontend dependencies unavailable                                                                                             | frontend    | run after dependency installation                                    |
| `npm --prefix apps/web run typecheck`    | frontend dependencies unavailable                                                                                             | frontend    | run after dependency installation                                    |
| `npm --prefix apps/web run test`         | frontend dependencies unavailable                                                                                             | frontend    | run deterministic component and MSW feature tests after installation |
| `npm --prefix apps/web run build`        | frontend dependencies unavailable                                                                                             | build       | run production build in CI                                           |
| `npm --prefix apps/web run e2e:mock`     | Playwright browsers/dependencies unavailable                                                                                  | e2e         | run mocked project-to-quality-gate smoke flow in CI                  |
| Live course generation                   | worker/database/model runtime unavailable                                                                                     | integration | run API/worker contract and generated-draft navigation tests         |
| Live question generation                 | worker/database/model runtime unavailable                                                                                     | integration | run API/worker contract and draft-bank navigation tests              |
| Live evaluation execution                | no Phase 9 FastAPI routes or worker runtime                                                                                   | integration | expose and test typed evaluation-run API contract                    |
| Production authentication integration    | identity provider/session host not selected                                                                                   | integration | configure bearer/session adapter and authorization tests             |

The 2026-07-23 static verification found that direct imports are declared by `apps/web/package.json`
and that the current frontend uses only the declared Next.js, React, TanStack Query, React Hook
Form/Zod, Vitest, Testing Library, and Playwright packages. It also confirmed that no web source
uses `dangerouslySetInnerHTML`, browser storage, or token logging. These static observations do
not replace lint, strict typecheck, tests, build, or browser verification. The FastAPI route file
contains more legacy course read/write routes than the Phase 10C limitations document describes;
their response contracts must be reconciled during the blocked runtime verification rather than
being inferred or fabricated in the browser.

The current backend lacks production list/detail/mutation contracts for course editor/version
validation and publication; question banks, questions, revisions, review queues, and duplicate
clusters; evaluation runs/results; golden datasets; quality-gate policies; and baselines. Phase
10C renders typed unavailable states for these capabilities rather than emulating successful
production behavior. `apps/web/tests/mocks` remains the only location for deterministic mock
fixtures; production routes do not consume them.

## Phase 10 frontend CI verification

| Check/category                                                            | Reason                                                                                                                                                             | Type            | Later execution                                                                                                                                       |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frozen frontend CI                                                        | `apps/web/package-lock.json` is committed, has npm lockfile format v3, and matches `package.json`; this environment receives HTTP 403 for locked tarball downloads | dependency / CI | Let `.github/workflows/frontend.yml` run `npm --prefix apps/web ci` and its frontend jobs in GitHub Actions                                           |
| Live FastAPI integration, production authentication, file upload, and SSE | The CI smoke suite deliberately uses mock-only public configuration and no service infrastructure                                                                  | integration     | Run against explicitly provisioned API, identity, object storage, worker, and event infrastructure without exposing secrets in `NEXT_PUBLIC_*` values |

The frontend workflow explicitly installs from `apps/web/package-lock.json` with
`npm --prefix apps/web ci`. It must not be reported as successful until that frozen install and its
jobs run successfully. Its mocked browser job is separate (not deferred) and will install Chromium,
run without Docker or a backend, and upload reports, screenshots, and traces on failure.
# Phase 11 learner verification

- Live PostgreSQL learner persistence and Alembic migration verification are deferred because Docker
  and PostgreSQL are unavailable.
- Real authentication/authorization, live API-to-browser learner flows, Redis/Celery asynchronous
  grading, code/SQL sandboxing, and production deployment verification are deferred.
- Mocked Playwright could not launch locally because the pinned Chromium binary is absent; an
  attempted `playwright install chromium` received HTTP 403 from the configured CDN.
