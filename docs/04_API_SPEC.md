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
