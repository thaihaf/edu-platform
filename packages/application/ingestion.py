"""Vendor-neutral ingestion orchestration and deterministic input processing."""

from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from packages.domain.models import (
    IngestionJob,
    IngestionStage,
    InputType,
    Source,
    SourceChunk,
    SourceSnapshot,
    StructuredContentBlock,
    StructuredDocument,
    StructuredSection,
)
from packages.domain.ports import (
    ChunkRepository,
    DocumentParser,
    EmbeddingProvider,
    IngestionJobRepository,
    ProgressEventPublisher,
)


class IngestionError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def canonicalize_url(value: str) -> str:
    """Validate syntactically; DNS resolution is intentionally a future port."""
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise IngestionError("INVALID_URL", "URL is malformed") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise IngestionError("INVALID_URL", "Only absolute HTTP(S) URLs are allowed")
    if parsed.username or parsed.password:
        raise IngestionError("INVALID_URL", "URL credentials are not allowed")
    host = parsed.hostname.lower()
    if host == "localhost" or re.fullmatch(r"(?:0x[0-9a-f]+|\d+)", host, re.I):
        raise IngestionError("URL_HOST_FORBIDDEN", "URL host is not publicly routable")
    try:
        address = ipaddress.ip_address(host)
        if not address.is_global:
            raise IngestionError("URL_HOST_FORBIDDEN", "URL host is not publicly routable")
    except ValueError:
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", host):
            raise IngestionError("INVALID_URL", "URL hostname is malformed") from None
    port = parsed.port
    netloc = (
        host
        if port is None
        or (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
        else f"{host}:{port}"
    )
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


class SimpleTokenizer:
    name = "simple-whitespace-v1"

    def count(self, text: str) -> int:
        return len(text.split())


@dataclass(frozen=True)
class ChunkingConfig:
    target_tokens: int = 300
    maximum_tokens: int = 400
    overlap_tokens: int = 30
    version: str = "structure-v1"


def chunk_document(
    document: StructuredDocument, snapshot_id: UUID, config: ChunkingConfig | None = None
) -> list[SourceChunk]:
    config = config or ChunkingConfig()
    tokenizer = SimpleTokenizer()
    config_hash = hashlib.sha256(repr(config).encode()).hexdigest()
    chunks: list[SourceChunk] = []
    for section in document.sections:
        buffer: list[str] = []
        for block in section.blocks:
            if block.kind not in {"paragraph", "table", "code", "list"} or not block.text.strip():
                continue
            candidate = "\n".join(buffer + [block.text])
            if buffer and tokenizer.count(candidate) > config.maximum_tokens:
                text = "\n".join(buffer)
                chunks.append(
                    _chunk(snapshot_id, len(chunks), text, section, tokenizer, config_hash, config)
                )
                tail = (
                    " ".join(text.split()[-config.overlap_tokens :])
                    if config.overlap_tokens
                    else ""
                )
                buffer = [tail, block.text] if tail else [block.text]
            else:
                buffer.append(block.text)
        if buffer:
            chunks.append(
                _chunk(
                    snapshot_id,
                    len(chunks),
                    "\n".join(buffer),
                    section,
                    tokenizer,
                    config_hash,
                    config,
                )
            )
    return chunks


def _chunk(
    snapshot: UUID,
    index: int,
    text: str,
    section: StructuredSection,
    tokenizer: SimpleTokenizer,
    config_hash: str,
    config: ChunkingConfig,
) -> SourceChunk:
    digest = hashlib.sha256(f"{snapshot}:{index}:{text}".encode()).hexdigest()
    return SourceChunk(
        snapshot,
        index,
        text,
        section.page_start,
        section.page_end,
        section.section_path,
        section.heading,
        tokenizer.count(text),
        digest,
        metadata_json={
            "tokenizer_name": tokenizer.name,
            "chunker_version": config.version,
            "chunking_configuration_hash": config_hash,
        },
    )


class TextDocumentParser:
    async def parse(
        self, content: bytes, mime_type: str, filename: str | None = None
    ) -> StructuredDocument:
        if mime_type != "text/plain":
            raise IngestionError("DOCUMENT_PARSE_FAILED", "Text parser only accepts text/plain")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IngestionError("INVALID_FILE_CONTENT", "Text must be UTF-8") from exc
        sections: list[StructuredSection] = []
        path: list[str] = []
        blocks: list[StructuredContentBlock] = []
        heading: str | None = None
        for paragraph in normalize_text(text).split("\n\n"):
            lines = paragraph.strip().splitlines()
            if lines and lines[0].startswith("#"):
                if blocks:
                    sections.append(
                        StructuredSection(
                            heading, 1 if heading else None, tuple(path), tuple(blocks)
                        )
                    )
                level = len(lines[0]) - len(lines[0].lstrip("#"))
                heading = lines[0][level:].strip()
                path = path[: level - 1] + [heading]
                blocks = []
            elif paragraph.strip():
                blocks.append(StructuredContentBlock("paragraph", paragraph.strip()))
        if blocks or not sections:
            sections.append(
                StructuredSection(heading, 1 if heading else None, tuple(path), tuple(blocks))
            )
        return StructuredDocument(
            filename, None, mime_type, "plain-text", "1", tuple(sections), page_count=1
        )


class IngestionService:
    def __init__(
        self,
        jobs: IngestionJobRepository,
        chunks: ChunkRepository,
        parser: DocumentParser,
        embeddings: EmbeddingProvider,
        events: ProgressEventPublisher,
    ):
        self.jobs, self.chunks, self.parser, self.embeddings, self.events = (
            jobs,
            chunks,
            parser,
            embeddings,
            events,
        )

    async def ingest_text(
        self,
        project_id: UUID,
        title: str,
        text: str,
        idempotency_key: str,
        trace_id: str,
        language: str | None = None,
    ) -> tuple[Source, SourceSnapshot, IngestionJob]:
        normalized = normalize_text(text)
        request_hash = hashlib.sha256(
            f"TEXT:{project_id}:{title}:{normalized}".encode()
        ).hexdigest()
        existing = await self.jobs.get_by_idempotency_key(idempotency_key)
        if existing:
            if getattr(existing, "request_hash", request_hash) != request_hash:
                raise IngestionError(
                    "IDEMPOTENCY_CONFLICT", "Idempotency key was reused with another payload"
                )
            raise IngestionError("SOURCE_DUPLICATE", str(existing.id))
        source = Source(project_id, "TEXT", title, language=language)
        snapshot = SourceSnapshot(
            source.id,
            1,
            None,
            hashlib.sha256(normalized.encode()).hexdigest(),
            {"original_text": text, "normalized": True},
        )
        job = await self.jobs.create(
            IngestionJob(
                project_id, source.id, snapshot.id, InputType.TEXT, idempotency_key, trace_id
            ),
            request_hash,
        )
        await self._run(job, snapshot, normalized.encode(), "text/plain")
        return source, snapshot, job

    async def register_url(
        self, project_id: UUID, url: str, title: str | None, idempotency_key: str, trace_id: str
    ) -> tuple[Source, IngestionJob]:
        canonical = canonicalize_url(url)
        request_hash = hashlib.sha256(f"URL:{project_id}:{canonical}".encode()).hexdigest()
        job = await self.jobs.create(
            IngestionJob(project_id, UUID(int=0), None, InputType.URL, idempotency_key, trace_id),
            request_hash,
        )
        source = Source(project_id, "URL", title or canonical, canonical_url=canonical)
        job.source_id = source.id
        job.complete()
        await self.jobs.update(job)
        await self._publish(job)
        return source, job

    async def _run(
        self, job: IngestionJob, snapshot: SourceSnapshot, content: bytes, mime_type: str
    ) -> None:
        try:
            for stage, pct in ((IngestionStage.HASHING, 15), (IngestionStage.PARSING, 35)):
                job.advance(stage, pct)
                await self.jobs.update(job)
                await self._publish(job)
            document = await self.parser.parse(content, mime_type)
            job.advance(IngestionStage.CHUNKING, 55)
            chunks = chunk_document(document, snapshot.id)
            job.advance(IngestionStage.EMBEDDING, 70)
            vectors = await self.embeddings.embed_texts([c.text for c in chunks])
            if any(len(v) != self.embeddings.vector_dimension for v in vectors):
                raise IngestionError(
                    "EMBEDDING_DIMENSION_MISMATCH", "Embedding dimension does not match provider"
                )
            enriched = [
                SourceChunk(
                    **{
                        **c.__dict__,
                        "embedding": tuple(v),
                        "embedding_model": self.embeddings.model_name,
                        "embedding_dimension": len(v),
                    }
                )
                for c, v in zip(chunks, vectors, strict=True)
            ]
            job.advance(IngestionStage.PERSISTING, 90)
            await self.chunks.create_chunks(enriched)
            job.complete()
            await self.jobs.update(job)
            await self._publish(job)
        except IngestionError as exc:
            job.fail(exc.code, str(exc))
            await self.jobs.update(job)
            await self._publish(job)
        except Exception:
            job.fail("DOCUMENT_PARSE_FAILED", "Source processing failed")
            await self.jobs.update(job)
            await self._publish(job)

    async def _publish(self, job: IngestionJob) -> None:
        try:
            await self.events.publish(job)
        except Exception:
            pass  # progress delivery is explicitly non-transactional
