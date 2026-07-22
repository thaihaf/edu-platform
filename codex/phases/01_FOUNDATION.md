# Phase 1 — Foundation

Create a working monorepo foundation.

## Deliverables

- `apps/api`: FastAPI application
- `apps/worker`: Celery worker
- `apps/web`: placeholder application and README
- `packages/domain`
- `packages/infrastructure`
- `packages/ai`
- Docker Compose with:
  - postgres + pgvector
  - redis
  - minio
  - searxng
- `.env.example`
- Makefile
- CI workflow
- health endpoints
- structured logging
- trace ID middleware

## Acceptance criteria

- `docker compose up` starts infrastructure.
- API `/health/live` and `/health/ready` work.
- Worker can connect to Redis.
- Unit test suite runs.
- Ruff and type checking pass.
- README has exact local setup commands.
