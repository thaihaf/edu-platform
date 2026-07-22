# Phase 3 — Ingestion

Implement ingestion for text, URL metadata placeholders and uploaded files.

## Requirements

- File upload to MinIO.
- SHA-256 content hashing.
- Duplicate detection.
- Docling parser adapter.
- Structured document output.
- Chunking preserving page and section path.
- Embedding provider interface.
- pgvector storage.
- Job progress events.
- Idempotent retries.

## Security

- MIME validation.
- Size limits.
- Safe filenames.
- SSRF-safe URL model even before crawling is implemented.
