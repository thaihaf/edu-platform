# Deterministic mock strategy

MSW handlers mirror the documented FastAPI envelope, including `error.code`, `details`, and
`trace_id`. Test scenarios cover successful responses, loading, validation, forbidden, empty,
long-running, and failed jobs. Add a handler beside its feature before adding a mocked journey;
mocks are transport fixtures, never a replacement for backend policy.
