# ADR 033: Production hardening boundaries

## Decision

Keep observability, rate limiting, error reporting, and RBAC as replaceable infrastructure
boundaries. The API provides a privacy-safe process fallback for metrics and rate limits, while a
production gateway/shared limiter and trusted identity adapter remain mandatory deployment concerns.

## Consequences

The repository can deterministically test policy without credentials or hosted vendors. Production
operators must configure OTLP, protected metrics access, managed secrets, shared limiting, and an
identity adapter; an arbitrary request header never grants a role.
