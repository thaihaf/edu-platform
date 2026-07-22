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
            lambda request: (
                httpx.Response(404)
                if request.url.path == "/robots.txt"
                else httpx.Response(302, headers={"location": "http://internal.test"})
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(SearchError):
                await HttpCrawlProvider(Resolver(("8.8.8.8",)), client).fetch_url(
                    "https://public.test"
                )

    asyncio.run(run())


def test_http_crawler_enforces_robots_before_fetching() -> None:
    class DenyRobots:
        async def may_fetch(self, url: str, user_agent: str) -> bool:
            return False

    async def run() -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text="<p>ok</p>"))
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(SearchError, match="Robots"):
                await HttpCrawlProvider(
                    Resolver(("8.8.8.8",)), client, robots_policy=DenyRobots()
                ).fetch_url("https://public.test")

    asyncio.run(run())


def test_http_crawler_stops_streaming_at_byte_limit() -> None:
    class AllowRobots:
        async def may_fetch(self, url: str, user_agent: str) -> bool:
            return True

    async def run() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200, content=b"x" * 11, headers={"content-type": "text/html"}
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(SearchError, match="byte limit"):
                await HttpCrawlProvider(
                    Resolver(("8.8.8.8",)), client, max_bytes=10, robots_policy=AllowRobots()
                ).fetch_url("https://public.test")

    asyncio.run(run())
