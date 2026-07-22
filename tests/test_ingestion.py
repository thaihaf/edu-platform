from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from fastapi.encoders import jsonable_encoder

from apps.api.app.main import source_snapshot_response
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
from packages.infrastructure.memory import MemoryRepository


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
            MemoryRepository(),
            MemoryRepository("snapshot_version"),
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


def test_text_parser_preserves_content_after_inline_heading() -> None:
    async def run() -> None:
        document = await TextDocumentParser().parse(b"# Intro\nBody", "text/plain")

        assert document.sections[0].heading == "Intro"
        assert document.sections[0].blocks[0].text == "Body"
        assert chunk_document(document, uuid4())

    asyncio.run(run())


def test_ingestion_persists_created_source_and_snapshot() -> None:
    async def run() -> None:
        chunks = InMemoryChunkRepository()
        jobs = InMemoryIngestionJobRepository()
        sources = MemoryRepository()
        snapshots = MemoryRepository("snapshot_version")
        service = IngestionService(
            jobs,
            chunks,
            TextDocumentParser(),
            DeterministicEmbeddingProvider(),
            InMemoryProgressPublisher(),
            sources,
            snapshots,
        )

        source, snapshot, _ = await service.ingest_text(
            uuid4(), "Notes", "Content", "key-2", "trace"
        )

        assert await sources.get(source.id) is source
        assert await snapshots.list_for_source(source.id) == [snapshot]

        url_source, _ = await service.register_url(
            uuid4(), "https://example.com", None, "key-3", "trace"
        )
        assert await sources.get(url_source.id) is url_source

    asyncio.run(run())


def test_snapshot_response_copies_immutable_metadata() -> None:
    from packages.domain.models import SourceSnapshot

    snapshot = SourceSnapshot(uuid4(), 1, None, "hash", {"normalized": True})

    response = source_snapshot_response(snapshot)

    assert response["metadata_json"] == {"normalized": True}
    assert isinstance(response["metadata_json"], dict)
    assert jsonable_encoder(response)["metadata_json"] == {"normalized": True}
