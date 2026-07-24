# Phase 12 — Production Hardening implementation plan

## Baseline

This work starts from the locally available latest integrated baseline (`work` at
`21fb5e0`).  This checkout has no `main` ref and no configured remote, so the
fresh `phase-12-production-hardening` branch is based on that commit. GitHub
Codespaces externally verified the mocked Playwright browser baseline on main.

## Plan

1. Add framework-neutral security and observability boundaries: role policy, bounded
   request rate limiting, trace-aware metrics, OpenTelemetry setup, and a scrubbed
   Sentry-compatible error-reporting adapter.
2. Wire the boundaries into FastAPI without granting a production identity from a
   browser/header fallback; retain deterministic development behavior for existing
   in-process tests.
3. Add production-safe environment validation and configuration documentation for
   telemetry, error reporting, rate limits, secret injection, and trusted identity
   integration.
4. Add focused security and operational tests plus a repeatable load-test scenario.
5. Document backup/restore and disaster recovery procedures, retention controls, and
   the optional Celery-to-Temporal migration decision. Record infrastructure-only
   verification explicitly rather than fabricating live integrations.

## Scope boundary

Phase 12 hardens existing APIs and operations. It does not add Phase 13 product
features, a production identity-provider integration, a hosted telemetry vendor,
or a Temporal runtime migration.
