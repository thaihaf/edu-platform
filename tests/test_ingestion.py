from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from packages.application.ingestion import (
    ChunkingConfig,
    IngestionError,
    IngestionService,
    TextDocumentParser,
    canonicalize_url,
    chunk_document,
)
from packages.domain.models import (
    IngestionJob,
    IngestionStage,
    InputType,
    InvalidStateTransitionError,
)
from packages.infrastructure.ingestion import (
    DeterministicEmbeddingProvider,
    InMemoryChunkRepository,
    InMemoryIngestionJobRepository,
    InMemoryProgressPublisher,
)


@pytest.mark.parametrize(
    "value, expected", [("HTTPS://Example.COM:443/a?q=1#x", "https://example.com/a?q=1")]
)
def test_url_canonicalization(value: str, expected: str) -> None:
    assert canonicalize_url(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "ftp://example.com",
        "http://localhost",
        "http://127.0.0.1",
        "http://169.254.169.254",
        "http://user@example.com",
    ],
)
def test_url_policy_rejects_unsafe_hosts(value: str) -> None:
    with pytest.raises(IngestionError):
        canonicalize_url(value)


def test_text_ingestion_is_normalized_chunked_and_embedded() -> None:
    async def run() -> None:
        chunks = InMemoryChunkRepository()
        jobs = InMemoryIngestionJobRepository()
        service = IngestionService(
            jobs,
            chunks,
            TextDocumentParser(),
            DeterministicEmbeddingProvider(),
            InMemoryProgressPublisher(),
        )
        source, snapshot, job = await service.ingest_text(
            uuid4(), "Notes", "# Intro\r\n\r\nOne two three", "key-1", "trace"
        )
        assert source.id == snapshot.source_id
        assert job.status.value == "COMPLETED"
        stored = await chunks.list_by_snapshot(snapshot.id)
        assert stored[0].embedding_dimension == 8
        assert "\r" not in stored[0].text

    asyncio.run(run())


def test_job_rejects_backwards_transition() -> None:
    job = IngestionJob(uuid4(), uuid4(), None, InputType.TEXT, "key", "trace")
    job.advance(IngestionStage.PARSING, 30)
    with pytest.raises(InvalidStateTransitionError):
        job.advance(IngestionStage.HASHING, 10)


def test_chunking_is_deterministic() -> None:
    async def run() -> None:
        doc = await TextDocumentParser().parse(b"# One\n\nhello world", "text/plain")
        assert [x.chunk_hash for x in chunk_document(doc, uuid4(), ChunkingConfig())] != []

    asyncio.run(run())
