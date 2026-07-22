# Phase 4 — Search and Crawling

Implement source discovery and fetching.

## Components

- SearchProvider interface.
- SearXNG adapter.
- Query family generator.
- Result fusion.
- Canonical URL normalization.
- CrawlProvider interface.
- Crawl4AI adapter.
- BrowserProvider interface with disabled-by-default browser-use adapter.
- Robots/access policy.
- SSRF protection.
- Snapshot storage.
- Source quality scoring.
- Near-duplicate detection.

## Tests

Use mocked providers. Do not require external internet for CI.
