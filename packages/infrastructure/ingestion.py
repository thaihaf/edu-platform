"""Deterministic test adapters and lazy optional production adapter boundaries."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator, Mapping
from uuid import UUID

from packages.domain.models import IngestionJob, SourceChunk


async def _bytes(data: bytes) -> AsyncIterator[bytes]:
    yield data


class InMemoryObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, dict[str, str]]] = {}

    async def put_object(
        self, key: str, content: AsyncIterator[bytes], metadata: Mapping[str, str]
    ) -> None:
        data = b"".join([part async for part in content])
        existing = self.objects.get(key)
        if existing and existing[0] != data:
            raise ValueError("object key already exists with different content")
        self.objects[key] = (data, dict(metadata))

    async def get_object(self, key: str) -> AsyncIterator[bytes]:
        return _bytes(self.objects[key][0])

    async def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    async def object_exists(self, key: str) -> bool:
        return key in self.objects

    async def get_object_metadata(self, key: str) -> Mapping[str, str]:
        return self.objects[key][1]


class DeterministicEmbeddingProvider:
    def __init__(self, dimension: int = 8) -> None:
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return "deterministic-sha256-v1"

    @property
    def vector_dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [
            [byte / 255 for byte in hashlib.sha256(text.encode()).digest()[: self._dimension]]
            for text in texts
        ]


class InMemoryChunkRepository:
    def __init__(self) -> None:
        self.chunks: dict[UUID, list[SourceChunk]] = {}

    async def create_chunks(self, chunks: list[SourceChunk]) -> None:
        if not chunks:
            return
        existing = await self.existing_hashes(chunks[0].source_snapshot_id)
        if any(chunk.chunk_hash in existing for chunk in chunks):
            return
        self.chunks.setdefault(chunks[0].source_snapshot_id, []).extend(chunks)

    async def list_by_snapshot(self, snapshot_id: UUID) -> list[SourceChunk]:
        return list(self.chunks.get(snapshot_id, []))

    async def existing_hashes(self, snapshot_id: UUID) -> set[str]:
        return {chunk.chunk_hash for chunk in self.chunks.get(snapshot_id, [])}


class InMemoryIngestionJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[UUID, IngestionJob] = {}
        self.keys: dict[str, tuple[str, UUID]] = {}

    async def create(self, job: IngestionJob, request_hash: str) -> IngestionJob:
        existing = self.keys.get(job.idempotency_key)
        if existing:
            if existing[0] != request_hash:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            return self.jobs[existing[1]]
        self.jobs[job.id] = job
        self.keys[job.idempotency_key] = (request_hash, job.id)
        job.request_hash = request_hash
        return job

    async def get(self, job_id: UUID) -> IngestionJob | None:
        return self.jobs.get(job_id)

    async def get_by_idempotency_key(self, key: str) -> IngestionJob | None:
        item = self.keys.get(key)
        return self.jobs.get(item[1]) if item else None

    async def update(self, job: IngestionJob) -> None:
        self.jobs[job.id] = job

    async def get_resumable_job(self, job_id: UUID) -> IngestionJob | None:
        job = self.jobs.get(job_id)
        return job if job and job.status.value in {"PENDING", "RUNNING", "FAILED"} else None


class InMemoryProgressPublisher:
    def __init__(self) -> None:
        self.events: dict[UUID, list[dict[str, object]]] = {}

    async def publish(self, job: IngestionJob) -> None:
        self.events.setdefault(job.id, []).append(
            {
                "stage": job.stage.value,
                "status": job.status.value,
                "progress_percent": job.progress_percent,
            }
        )


class DoclingDocumentParser:
    """Lazy Docling adapter; real conversion is an integration-only concern."""

    async def parse(self, content: bytes, mime_type: str, filename: str | None = None) -> object:
        try:
            from docling.document_converter import DocumentConverter  # noqa: I001
        except ImportError as exc:
            raise RuntimeError("Docling is not installed; install the docling extra") from exc
        DocumentConverter()
        raise NotImplementedError("Docling conversion requires a temporary file adapter")
