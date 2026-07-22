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
