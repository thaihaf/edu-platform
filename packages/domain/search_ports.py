from __future__ import annotations

from typing import Protocol

from packages.domain.search import NormalizedWebDocument, SearchOptions, SearchResultPage


class SearchProvider(Protocol):
    @property
    def provider_name(self) -> str: ...
    @property
    def supported_capabilities(self) -> frozenset[str]: ...
    async def search(self, query: str, options: SearchOptions) -> SearchResultPage: ...


class CrawlProvider(Protocol):
    async def fetch_url(self, url: str) -> bytes: ...
    async def crawl_page(self, url: str) -> NormalizedWebDocument: ...
    async def extract_content(self, content: bytes, url: str) -> NormalizedWebDocument: ...


class BrowserProvider(Protocol):
    async def fetch_rendered_page(self, url: str) -> NormalizedWebDocument: ...
    async def interact(self, url: str, actions: tuple[str, ...]) -> NormalizedWebDocument: ...


class DNSResolver(Protocol):
    async def resolve(self, hostname: str) -> tuple[str, ...]: ...


class RobotsPolicyProvider(Protocol):
    async def may_fetch(self, url: str, user_agent: str) -> bool: ...


class ContentNormalizer(Protocol):
    async def normalize(
        self, content: bytes, requested_url: str, final_url: str, http_metadata: dict[str, object]
    ) -> NormalizedWebDocument: ...
