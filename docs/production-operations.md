# Production operations

## Telemetry and errors

Set `OTEL_EXPORTER_OTLP_ENDPOINT` to a collector endpoint. The API emits trace-aware structured
logs and configures OTLP tracing when the optional OpenTelemetry SDK is installed. `/metrics`
exports a small Prometheus-compatible process metric set; production requires `METRICS_TOKEN` and
only accepts it as a bearer token. Keep this endpoint on a private network in addition to the token.

Set `SENTRY_DSN` only through the deployment secret store. The bundled Sentry-compatible boundary
records exception type and trace ID, not request bodies, authorization headers, source content, or
environment values. A hosted Sentry SDK transport may be installed at deployment after a privacy
review; do not put its DSN in browser configuration.

## Secrets and identity

Inject `DATABASE_URL`, Redis credentials, MinIO credentials, model credentials, `SENTRY_DSN`, and
`METRICS_TOKEN` from a managed secret store (Kubernetes Secrets encrypted with KMS, Vault, or cloud
equivalent). Rotate access keys at least every 90 days, revoke immediately on exposure, and use
least-privilege service accounts. `.env` is local development only and must never be baked into an
image or committed.

The application role policy defines ADMIN, RESEARCHER, REVIEWER, EDITOR, and VIEWER. Production must
install a trusted bearer/session identity adapter that validates issuer, audience, signature,
expiration, and tenant/workspace claims before calling the policy. Client role checks and arbitrary
headers are never identity evidence.

## Rate limits and retention

`RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` configure a process-local safety fallback.
Production must enforce the equivalent limit at the gateway and use a shared Redis limiter so a
multi-replica deployment cannot be bypassed. Preserve only hashed limiter keys in process memory.

Keep request logs for 30 days, operational metrics for 90 days, error events for 30 days, and audit
records according to the approved legal retention schedule. Configure object-storage lifecycle rules
for source originals and backups; legal holds override deletion. Perform a quarterly retention review.

## Backup, restore, and disaster recovery

1. Take encrypted daily PostgreSQL logical backups and point-in-time recovery WAL archives; encrypt
   object storage with a separate key and versioning enabled.
2. Copy backups to a separate account/region with immutable retention and test a restore monthly.
3. Before restore, declare an incident, freeze writes, preserve logs/audit evidence, and choose a
   recovery point.
4. Restore into an isolated environment, run migrations, verify counts/checksums and health/readiness,
   then switch traffic only after an owner approves the validation record.
5. Rotate all credentials after an incident and document RPO/RTO results. Initial targets are RPO 24h
   and RTO 8h until a live exercise establishes stricter values.

## Optional Temporal migration

Celery remains the current worker runtime. Consider Temporal only when durable long-running workflow
execution, cross-service compensation, or operational visibility cannot be met with the existing
checkpoint and idempotency ports. Keep application workflow ports stable, add a Temporal adapter in
parallel, replay representative jobs in a non-production namespace, then migrate one workflow behind
a feature flag. Do not run Celery and Temporal for the same idempotency key.
