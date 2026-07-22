# API Specification

Base path: `/api/v1`

## Projects

- POST `/projects`
- GET `/projects/{id}`
- PATCH `/projects/{id}`
- POST `/projects/{id}/start-research`
- GET `/projects/{id}/progress`
- POST `/projects/{id}/cancel`

## Sources

- POST `/projects/{id}/sources/url`
- POST `/projects/{id}/sources/text`
- POST `/projects/{id}/sources/file`
- GET `/projects/{id}/sources`
- GET `/sources/{source_id}`
- POST `/sources/{source_id}/refetch`
- PATCH `/sources/{source_id}/review`

## Research

- GET `/projects/{id}/research-brief`
- GET `/projects/{id}/queries`
- GET `/projects/{id}/claims`
- GET `/projects/{id}/gaps`
- POST `/projects/{id}/follow-up-research`

## Course

- POST `/projects/{id}/generate-course`
- GET `/courses/{course_id}`
- GET `/courses/{course_id}/versions`
- POST `/courses/{course_id}/versions/{version_id}/publish`
- POST `/courses/{course_id}/versions/{version_id}/rollback`
- GET `/courses/{course_id}/versions/{version_id}/diff`

## Questions

- POST `/projects/{id}/mine-questions`
- POST `/projects/{id}/generate-questions`
- GET `/projects/{id}/questions`
- PATCH `/questions/{question_id}/review`
- POST `/questions/{question_id}/re-evaluate`

## Evaluation

- POST `/projects/{id}/evaluate`
- GET `/projects/{id}/evaluation-runs`
- GET `/evaluation-runs/{id}`

## Events

- GET `/jobs/{job_id}/events` using SSE.

## Error format

```json
{
  "error": {
    "code": "SOURCE_FETCH_FAILED",
    "message": "Unable to fetch source",
    "details": {},
    "trace_id": "..."
  }
}
```

## Phase 2 implemented domain endpoints

Phase 2 implements the domain-data subset under `/api/v1`: workspace creation and
lookup; project create/read/update; source create/list/read; immutable snapshot
create/list; course create/read; and course-version create/list/read/edit/publish.
Snapshots have no update route. Editing a non-draft course version returns the
standard `409 CONFLICT` error contract. Create operations return `201`; reads and
updates return `200`.

## Phase 3 ingestion endpoints

`POST /projects/{id}/sources/text` accepts title, text, optional language and metadata,
and requires `Idempotency-Key`; it returns `202` with source, immutable snapshot, and
job representations. `POST /projects/{id}/sources/url` validates and registers a
canonical HTTP(S) URL only—Phase 3 never fetches it. `GET /ingestion-jobs/{id}` and
`GET /ingestion-jobs/{id}/events` return in-process job state and persisted-style
event records; `GET /sources/{source_id}/snapshots/{snapshot_id}/chunks` returns safe
chunk metadata without object-storage URLs.

## Phase 4 search and fetch endpoints
- `POST /projects/{project_id}/search-queries`; `POST /projects/{project_id}/search-queries/batch`
- `POST /search-queries/{query_id}/execute`; `GET /projects/{project_id}/search-queries`; `GET /search-queries/{query_id}`; `GET /search-queries/{query_id}/results`
- `POST /search-results/{result_id}/accept`
- `POST /sources/{source_id}/fetch` requires `Idempotency-Key` and returns `202`; `GET /fetch-jobs/{job_id}` and `/events`
- `GET /sources/{source_id}/snapshots` and `/snapshots/{snapshot_id}` never return object-storage credentials.

## Phase 5 research jobs
`POST /projects/{project_id}/research-jobs` requires `Idempotency-Key` and returns `202`; it only
queues a workflow state and never executes research in the request. Job status, events, brief,
queries, sources, observations, coverage, gaps and result are available under `/research-jobs/{id}`.
`cancel`, `resume`, and `retry` are explicit job-control operations and return structured errors with trace IDs.

## Phase 6 evidence and knowledge
Evidence build is `POST /research-jobs/{job_id}/build-evidence` with `Idempotency-Key`. Claims,
evidence, contradictions, confidence recalculation and reviews are exposed at `/claims`; review
history is available at `/review-decisions`. Responses retain the standard typed error and trace-ID contract.
