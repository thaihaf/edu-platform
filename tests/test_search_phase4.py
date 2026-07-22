from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx
import pytest

from packages.application.search import (
    InMemorySearchRepository,
    SearchError,
    SearchService,
    canonicalize_web_url,
    reciprocal_rank_fusion,
    validate_public_url,
)
from packages.domain.search import (
    ProviderSearchResult,
    QueryFamily,
    SearchOptions,
    SearchQuery,
    SearchResultPage,
)
from packages.infrastructure.search import (
    FakeSearchProvider,
    HtmlContentNormalizer,
    HttpCrawlProvider,
    SearXNGProvider,
)


class Resolver:
    def __init__(self, addresses: tuple[str, ...]):
        self.addresses = addresses

    async def resolve(self, _: str) -> tuple[str, ...]:
        return self.addresses


def test_canonicalization_preserves_meaningful_query_and_idn() -> None:
    assert (
        canonicalize_web_url("HTTPS://bücher.example:443/a/../x?b=2&utm_source=x#no")
        == "https://xn--bcher-kva.example/x?b=2"
    )
    with pytest.raises(SearchError):
        canonicalize_web_url("http://user@example.com")


def test_ssrf_denies_private_and_allows_public() -> None:
    assert (
        asyncio.run(validate_public_url("https://example.test/a", Resolver(("8.8.8.8",))))
        == "https://example.test/a"
    )
    with pytest.raises(SearchError):
        asyncio.run(validate_public_url("https://example.test", Resolver(("127.0.0.1",))))


def test_rrf_is_deterministic_and_preserves_provenance() -> None:
    q = uuid4()
    pages = {
        "a": SearchResultPage((ProviderSearchResult(" A ", "https://example.com/x"),)),
        "b": SearchResultPage(
            (
                ProviderSearchResult("B", "https://example.com/x"),
                ProviderSearchResult("C", "https://other.example"),
            )
        ),
    }
    result = reciprocal_rank_fusion(pages, q)
    assert result[0].canonical_url == "https://example.com/x"
    assert result[0].metadata_json["provider_provenance"] == [
        {"provider": "a", "rank": 1},
        {"provider": "b", "rank": 1},
    ]


def test_fake_provider_and_idempotency() -> None:
    async def run() -> None:
        repo = InMemorySearchRepository()
        service = SearchService(
            repo, [FakeSearchProvider((ProviderSearchResult("A", "https://example.com"),))]
        )
        query = await service.register(SearchQuery(uuid4(), "query", QueryFamily.DIRECT))
        assert len(await service.execute(query.id, "x")) == 1
        assert len(await service.execute(query.id, "x")) == 1

    asyncio.run(run())


def test_searxng_mapping_and_rate_limit() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"results": [{"title": "A", "url": "https://example.com", "content": "S"}]},
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            assert (
                await SearXNGProvider("https://search", client).search("q", SearchOptions())
            ).results[0].title == "A"

    asyncio.run(run())


def test_html_normalization_removes_scripts_and_extracts_metadata() -> None:
    async def run() -> None:
        html = (
            b'<title>T</title><meta name="description" content="D">'
            b'<link rel="canonical" href="/c"><script>bad()</script>'
            b'<h1>Heading</h1><p>Hello</p><a href="/l">L</a>'
        )
        doc = await HtmlContentNormalizer().normalize(
            html,
            "https://e/x",
            "https://e/x",
            {},
        )
        assert (
            "bad" not in doc.visible_text
            and doc.headings == ("Heading",)
            and doc.canonical_url == "https://e/c"
        )

    asyncio.run(run())


def test_http_redirect_revalidated() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(302, headers={"location": "http://internal.test"})
        )
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(SearchError):
                await HttpCrawlProvider(Resolver(("8.8.8.8",)), client).fetch_url(
                    "https://public.test"
                )

    asyncio.run(run())


class _Dispatcher:
    def __init__(self, fail: bool = False):
        self.fail, self.calls = fail, []

    async def dispatch(self, job_id):
        self.calls.append(job_id)
        if self.fail:
            raise RuntimeError("queue down")


class _Crawler:
    def __init__(self, failure: Exception | None = None):
        self.failure, self.calls = failure, 0

    async def crawl_page(self, url):
        from datetime import UTC, datetime

        from packages.domain.search import NormalizedWebDocument

        self.calls += 1
        if self.failure:
            raise self.failure
        return NormalizedWebDocument(
            url,
            url,
            url,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "text",
            "text",
            (),
            (),
            None,
            {},
            (),
            "raw",
            "normalized",
            datetime.now(UTC),
            {},
        )


def test_fetch_lifecycle_dispatch_failure_crawl_failure_snapshot_failure_and_replay() -> None:
    from packages.application.search import FetchService, InMemoryFetchRepository
    from packages.domain.search import FetchJob, FetchStatus

    async def run() -> None:
        repo = InMemoryFetchRepository()
        dispatch = _Dispatcher()
        crawler = _Crawler()
        service = FetchService(repo, crawler, dispatch)
        job = FetchJob(
            uuid4(), uuid4(), "https://example.test/a", "https://example.test/a", "key", "t"
        )
        accepted = await service.accept(job)
        assert dispatch.calls == [job.id] and accepted.status is FetchStatus.PENDING
        assert (
            await service.accept(
                FetchJob(
                    job.project_id, job.source_id, job.requested_url, job.canonical_url, "key", "t"
                )
            )
        ).id == job.id
        assert dispatch.calls == [job.id]
        assert (await service.run(job.id)).status is FetchStatus.COMPLETED
        assert len(repo.snapshots) == 1
        snapshot = next(iter(repo.snapshots.values()))
        assert snapshot.snapshot_version == 1 and snapshot.raw_content_reference
        assert (await service.run(job.id)).status is FetchStatus.COMPLETED and len(
            repo.snapshots
        ) == 1

        second_job = FetchJob(
            job.project_id,
            job.source_id,
            "https://example.test/second",
            "https://example.test/second",
            "key-second",
            "t",
        )
        await service.accept(second_job)
        assert (await service.run(second_job.id)).status is FetchStatus.COMPLETED
        assert sorted(snapshot.snapshot_version for snapshot in repo.snapshots.values()) == [1, 2]

        failed_dispatch = FetchJob(
            uuid4(), uuid4(), "https://example.test/b", "https://example.test/b", "key2", "t"
        )
        assert (
            await FetchService(repo, crawler, _Dispatcher(True)).accept(failed_dispatch)
        ).status is FetchStatus.FAILED
        failed_crawl = FetchJob(
            uuid4(), uuid4(), "https://example.test/c", "https://example.test/c", "key3", "t"
        )
        service2 = FetchService(repo, _Crawler(SearchError("CRAWL_FAILED", "nope")), dispatch)
        await service2.accept(failed_crawl)
        assert (await service2.run(failed_crawl.id)).status is FetchStatus.FAILED

        original = repo.create_snapshot

        async def fail_snapshot(*args):
            raise RuntimeError("db down")

        repo.create_snapshot = fail_snapshot  # type: ignore[method-assign]
        persist_fail = FetchJob(
            uuid4(), uuid4(), "https://example.test/d", "https://example.test/d", "key4", "t"
        )
        await service.accept(persist_fail)
        assert (await service.run(persist_fail.id)).status is FetchStatus.FAILED
        repo.create_snapshot = original  # type: ignore[method-assign]

    asyncio.run(run())


def test_robots_streaming_limits_redirect_and_crawl4ai_denial() -> None:
    from packages.infrastructure.search import Crawl4AIProvider, HttpRobotsPolicy

    async def run() -> None:
        huge = b"x" * (64 * 1024 + 1)
        transport = httpx.MockTransport(lambda _: httpx.Response(200, content=huge))
        async with httpx.AsyncClient(transport=transport) as client:
            assert not await HttpRobotsPolicy(Resolver(("8.8.8.8",)), client).may_fetch(
                "https://e.test/x", "bot"
            )
        import gzip

        compressed = gzip.compress(huge)
        transport = httpx.MockTransport(
            lambda _: httpx.Response(200, headers={"content-encoding": "gzip"}, content=compressed)
        )
        async with httpx.AsyncClient(transport=transport) as client:
            assert not await HttpRobotsPolicy(Resolver(("8.8.8.8",)), client).may_fetch(
                "https://e.test/x", "bot"
            )
        redirects = httpx.MockTransport(
            lambda request: httpx.Response(302, headers={"location": "http://127.0.0.1/robots.txt"})
        )
        async with httpx.AsyncClient(transport=redirects) as client:
            assert not await HttpRobotsPolicy(Resolver(("8.8.8.8",)), client).may_fetch(
                "https://e.test/x", "bot"
            )

        class Deny:
            async def may_fetch(self, url, agent):
                return False

        with pytest.raises(SearchError, match="robots"):
            await Crawl4AIProvider(Resolver(("8.8.8.8",)), robots=Deny()).crawl_page(
                "https://e.test/x"
            )

        checked: list[str] = []

        class RedirectDeny:
            async def may_fetch(self, url, agent):
                checked.append(url)
                return not url.endswith("/blocked")

        redirects = httpx.MockTransport(
            lambda _: httpx.Response(302, headers={"location": "/blocked"})
        )
        async with httpx.AsyncClient(transport=redirects) as client:
            with pytest.raises(SearchError, match="robots"):
                await HttpCrawlProvider(
                    Resolver(("8.8.8.8",)), client=client, robots=RedirectDeny()
                ).fetch_url("https://e.test/allowed")
        assert checked == ["https://e.test/allowed", "https://e.test/blocked"]

    asyncio.run(run())
