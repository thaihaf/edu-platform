# Phase 2 — Domain and Data

Implement the domain model from `docs/03_DATA_MODEL.md`.

## Requirements

- Use UUIDs.
- Add timestamps.
- Use enums for statuses and origin types.
- Use immutable source snapshots.
- Implement repositories through interfaces.
- Add Alembic migrations.
- Add CRUD APIs for projects, sources and courses.
- Add audit event recording.

## Tests

- Model constraints.
- Repository behavior.
- API validation.
- Course version immutability.
- Published version cannot be edited.
