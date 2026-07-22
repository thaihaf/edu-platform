# Phase 4 — Search and crawling implementation plan

## Plan
1. Define provider-neutral search, crawl, robots, DNS, browser and content-normalization
   ports plus immutable domain models and fetch/query state machines.
2. Implement deterministic URL canonicalization, SSRF validation, robots evaluation,
   HTML normalization, result normalization/fusion, duplicate clustering and quality scoring.
3. Add mocked-testable SearXNG, HTTP/Crawl4AI and disabled-browser infrastructure adapters,
   with in-memory repositories and retry-safe application services.
4. Expose the Phase 4 `/api/v1` query, result-acceptance, fetch and snapshot endpoints;
   add SQLAlchemy mappings and an Alembic migration.
5. Document policies and environment configuration; run offline checks only, recording
   Docker-backed integration verification as deferred.

## Scope boundary
This phase discovers and safely fetches public sources. It does not plan queries with
AI, extract claims, construct graphs, or generate learning content.
