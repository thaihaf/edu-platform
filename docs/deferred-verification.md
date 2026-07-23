# Deferred verification

Docker is unavailable in this execution environment, so no Docker command was run or installed.

| Check/category | Reason | Type | Later execution |
|---|---|---|---|
| `docker compose config` runtime validation | Docker unavailable | environmental | `docker compose config` in a Docker-enabled runner |
| PostgreSQL repository integration tests (`integration`) | no PostgreSQL service | environmental | `pytest -m integration` against Compose PostgreSQL |
| Alembic upgrade/downgrade on PostgreSQL | no PostgreSQL service | environmental | `alembic upgrade head && alembic downgrade base` |
| Redis readiness and Celery broker ping | Docker unavailable | environmental | run Compose then health/worker checks |
| MinIO and SearXNG connectivity | Docker unavailable | environmental | run Compose service probes |
| MinIO source-object upload integration | Docker unavailable | environmental | exercise S3-compatible adapter against Compose MinIO |
| PostgreSQL source-chunk persistence and pgvector extension/dimension behavior | no PostgreSQL service | environmental | run `pytest -m integration` against pgvector PostgreSQL |
| Docling PDF/DOCX real-file conversion | optional Docling dependency/integration fixtures unavailable | environmental | install `.[docling]` and run parser integration tests |
| Celery/Redis ingestion execution and API-to-worker end-to-end ingestion | Docker unavailable | environmental | run Compose worker and e2e suite |

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
