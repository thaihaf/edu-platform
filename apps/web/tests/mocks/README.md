# Deterministic mock strategy

MSW handlers mirror the documented FastAPI envelope, including `error.code`, `details`, and
`trace_id`. Test scenarios cover successful responses, loading, validation, forbidden, empty,
long-running, and failed jobs. Add a handler beside its feature before adding a mocked journey;
mocks are transport fixtures, never a replacement for backend policy.

## Phase 10B fixtures

When dependencies are available, add MSW fixtures for the documented project detail, source
list/text-ingestion/job polling, research job/control, and claim/review endpoints. Fixtures must
include the FastAPI error envelope and trace ID. Missing production list endpoints must be tested
as the UI's explicit availability state, not replaced with fabricated success fixtures.
