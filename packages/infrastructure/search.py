from __future__ import annotations

import asyncio
import hashlib
import socket
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx

from packages.application.search import SearchError, canonicalize_web_url, validate_public_url
from packages.domain.search import (
    NormalizedWebDocument,
    ProviderSearchResult,
    SearchOptions,
    SearchResultPage,
)


class SystemDNSResolver:
    async def resolve(self, hostname: str) -> tuple[str, ...]:
        values = await asyncio.get_running_loop().run_in_executor(
            None, lambda: socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        )
        return tuple(sorted({item[4][0] for item in values}))


class SearXNGProvider:
    def __init__(self, endpoint: str, client: httpx.AsyncClient | None = None, timeout: float = 5):
        self.endpoint, self.client, self.timeout = endpoint.rstrip("/"), client, timeout

    @property
    def provider_name(self) -> str:
        return "searxng"

    @property
    def supported_capabilities(self) -> frozenset[str]:
        return frozenset({"locale", "language", "safe_search", "pagination", "domains"})

    async def search(self, query: str, options: SearchOptions) -> SearchResultPage:
        params = {
            "q": query,
            "format": "json",
            "pageno": options.page,
            "safesearch": int(options.safe_search),
            "language": options.language or "all",
        }
        try:
            if self.client:
                response = await self.client.get(
                    f"{self.endpoint}/search", params=params, timeout=self.timeout
                )
            else:
                async with httpx.AsyncClient(follow_redirects=False) as c:
                    response = await c.get(
                        f"{self.endpoint}/search", params=params, timeout=self.timeout
                    )
            if response.status_code == 429:
                raise SearchError("SEARCH_RATE_LIMITED", "Search provider rate limited request")
            response.raise_for_status()
            payload = response.json()
            rows = payload["results"]
            if not isinstance(rows, list):
                raise ValueError
        except httpx.TimeoutException as exc:
            raise SearchError("SEARCH_PROVIDER_UNAVAILABLE", "Search provider timed out") from exc
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise SearchError(
                "SEARCH_PROVIDER_UNAVAILABLE", "Search provider response unavailable"
            ) from exc
        return SearchResultPage(
            tuple(
                ProviderSearchResult(
                    str(x.get("title", "")),
                    str(x["url"]),
                    str(x.get("content", "")),
                    content_type=x.get("content_type"),
                    metadata={"raw": x},
                )
                for x in rows[: options.result_limit]
            )
        )


class FakeSearchProvider:
    def __init__(self, results: tuple[ProviderSearchResult, ...], name: str = "fake"):
        self.results, self.name = results, name

    @property
    def provider_name(self) -> str:
        return self.name

    @property
    def supported_capabilities(self) -> frozenset[str]:
        return frozenset()

    async def search(self, query: str, options: SearchOptions) -> SearchResultPage:
        return SearchResultPage(self.results[: options.result_limit])


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.text = []
        self.headings = []
        self.links = []
        self.meta = {}
        self.canonical = None
        self.title = None
        self._heading = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"script", "style", "noscript"} or a.get("hidden") is not None:
            self.skip += 1
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading = tag
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "meta" and a.get("name") in {
            "description",
            "author",
            "publisher",
            "date",
            "article:published_time",
        }:
            self.meta[a["name"]] = a.get("content", "")
        if tag == "meta" and a.get("property") in {"og:title", "og:description"}:
            self.meta[a["property"]] = a.get("content", "")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1
        if tag == self._heading:
            self._heading = None

    def handle_data(self, data):
        if not self.skip and data.strip():
            clean = " ".join(data.split())
            self.text.append(clean)
            if self._heading:
                self.headings.append(clean)
            if self.lasttag == "title":
                self.title = clean


class HtmlContentNormalizer:
    async def normalize(
        self, content: bytes, requested_url: str, final_url: str, http_metadata: dict[str, object]
    ) -> NormalizedWebDocument:
        raw = hashlib.sha256(content).hexdigest()
        parser = _Text()
        parser.feed(content.decode("utf-8", errors="replace"))
        text = "\n".join(parser.text)
        canonical = (
            canonicalize_web_url(urljoin(final_url, parser.canonical))
            if parser.canonical
            else canonicalize_web_url(final_url)
        )
        return NormalizedWebDocument(
            requested_url,
            final_url,
            canonical,
            parser.title or parser.meta.get("og:title"),
            parser.meta.get("description") or parser.meta.get("og:description"),
            parser.meta.get("author"),
            parser.meta.get("publisher"),
            None,
            None,
            None,
            text,
            "\n\n".join(f"# {x}" for x in parser.headings) + ("\n\n" + text if text else ""),
            tuple(parser.headings),
            tuple(urljoin(final_url, x) for x in parser.links),
            parser.canonical,
            parser.meta,
            (),
            raw,
            hashlib.sha256(text.encode()).hexdigest(),
            datetime.now().astimezone(),
            http_metadata,
        )


class DisabledBrowserProvider:
    async def fetch_rendered_page(self, url: str):
        raise SearchError("BROWSER_PROVIDER_DISABLED", "Browser provider is disabled by policy")

    async def interact(self, url: str, actions: tuple[str, ...]):
        raise SearchError("BROWSER_PROVIDER_DISABLED", "Browser provider is disabled by policy")


class HttpRobotsPolicy:
    """Fail-closed robots client with redirect-by-redirect SSRF validation."""

    max_bytes = 64 * 1024

    def __init__(
        self,
        resolver: SystemDNSResolver,
        client: httpx.AsyncClient | None = None,
        timeout: float = 5,
    ):
        self.resolver, self.client, self.timeout = resolver, client, timeout

    async def may_fetch(self, url: str, user_agent: str) -> bool:
        from urllib.parse import urlsplit
        from urllib.robotparser import RobotFileParser

        try:
            safe = await validate_public_url(url, self.resolver)
            base = urlsplit(safe)
            current = f"{base.scheme}://{base.netloc}/robots.txt"
            redirects = 0
            while True:
                current = await validate_public_url(current, self.resolver)
                response = await self._get(current)
                if response.is_redirect:
                    redirects += 1
                    location = response.headers.get("location")
                    if not location or redirects > 5:
                        return False
                    current = urljoin(current, location)
                    continue
                if response.status_code == 404:
                    return True
                if response.status_code != 200:
                    return False
                content = await self._read_limited(response)
                parser = RobotFileParser()
                parser.parse(content.decode("utf-8", errors="replace").splitlines())
                return parser.can_fetch(user_agent, safe)
        except (httpx.HTTPError, SearchError, ValueError, UnicodeError):
            return False

    async def _get(self, url: str) -> httpx.Response:
        # The hostname URL is retained so HTTP Host and HTTPS SNI remain the original host.
        # validate_public_url resolves and validates every target before each connection.
        headers = {"Host": urlsplit(url).netloc, "User-Agent": "ai-course-research-bot/0.1"}
        if self.client:
            return await self.client.get(
                url, follow_redirects=False, headers=headers, timeout=self.timeout
            )
        async with httpx.AsyncClient(follow_redirects=False, timeout=self.timeout) as client:
            return await client.get(url, headers=headers)

    async def _read_limited(self, response: httpx.Response) -> bytes:
        declared = response.headers.get("content-length")
        if declared and int(declared) > self.max_bytes:
            raise ValueError("robots response exceeds limit")
        content = bytearray()
        async for chunk in response.aiter_bytes():  # decoded bytes: limit is post-decompression
            content.extend(chunk)
            if len(content) > self.max_bytes:
                raise ValueError("robots response exceeds limit")
        return bytes(content)


class HttpCrawlProvider:
    def __init__(
        self,
        resolver: SystemDNSResolver,
        normalizer: HtmlContentNormalizer | None = None,
        client: httpx.AsyncClient | None = None,
        max_bytes: int = 2_000_000,
        redirect_limit: int = 5,
        robots: HttpRobotsPolicy | None = None,
    ):
        self.resolver, self.normalizer, self.client, self.max_bytes, self.redirect_limit = (
            resolver,
            normalizer or HtmlContentNormalizer(),
            client,
            max_bytes,
            redirect_limit,
        )
        self.robots = robots

    async def fetch_url(self, url: str) -> bytes:
        if self.robots and not await self.robots.may_fetch(url, "ai-course-research-bot/0.1"):
            raise SearchError("ROBOTS_DENIED", "robots.txt disallows this URL")
        current = url
        redirects = 0
        while True:
            await validate_public_url(current, self.resolver)
            try:
                if self.client:
                    response = await self.client.get(
                        current,
                        follow_redirects=False,
                        headers={"User-Agent": "ai-course-research-bot/0.1"},
                    )
                else:
                    async with httpx.AsyncClient(follow_redirects=False, cookies=None) as c:
                        response = await c.get(
                            current, headers={"User-Agent": "ai-course-research-bot/0.1"}
                        )
            except httpx.TimeoutException as exc:
                raise SearchError("FETCH_TIMEOUT", "Fetch timed out") from exc
            except httpx.HTTPError as exc:
                raise SearchError("FETCH_FAILED", "Fetch failed") from exc
            if response.is_redirect:
                redirects += 1
                if redirects > self.redirect_limit:
                    raise SearchError("REDIRECT_LIMIT_EXCEEDED", "Redirect limit exceeded")
                location = response.headers.get("location")
                if not location:
                    raise SearchError("FETCH_FAILED", "Malformed redirect")
                current = urljoin(current, location)
                continue
            if response.headers.get("content-type", "").split(";", 1)[0] not in {
                "text/html",
                "application/xhtml+xml",
            }:
                raise SearchError("UNSUPPORTED_CONTENT_TYPE", "Response type is unsupported")
            data = response.content
            if len(data) > self.max_bytes:
                raise SearchError("RESPONSE_TOO_LARGE", "Response exceeds byte limit")
            return data

    async def crawl_page(self, url: str) -> NormalizedWebDocument:
        return await self.extract_content(await self.fetch_url(url), url)

    async def extract_content(self, content: bytes, url: str) -> NormalizedWebDocument:
        return await self.normalizer.normalize(content, url, url, {"content_type": "text/html"})


class Crawl4AIProvider(HttpCrawlProvider):
    """Optional Crawl4AI boundary; import is intentionally delayed to runtime."""

    async def crawl_page(self, url: str) -> NormalizedWebDocument:
        await validate_public_url(url, self.resolver)
        if self.robots and not await self.robots.may_fetch(url, "ai-course-research-bot/0.1"):
            raise SearchError("ROBOTS_DENIED", "robots.txt disallows this URL")
        try:
            from crawl4ai import AsyncWebCrawler  # type: ignore[import-not-found]
        except ImportError as exc:
            raise SearchError(
                "CRAWL_FAILED", "Crawl4AI optional dependency is not installed"
            ) from exc
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
            html = getattr(result, "html", "").encode()
            document = await self.extract_content(html, url)
            return document
        except SearchError:
            raise
        except Exception as exc:
            raise SearchError("CRAWL_FAILED", "Crawl4AI failed") from exc
