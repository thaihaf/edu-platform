# Deferred container-runtime verification

Phase 1 container-runtime verification is deferred because Docker is not installed on this machine. Docker must **not** be installed as part of this work. The following checks remain required in a Docker-capable environment:

- `docker compose config`
- `docker compose up -d --build`
- container health checks
- live PostgreSQL and Redis readiness checks
- Celery ping through the real Redis broker
- MinIO connectivity
- SearXNG connectivity

These checks have not been run or passed locally. They must be executed against the repository's Compose configuration before accepting container integration.
