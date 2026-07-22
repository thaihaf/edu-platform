# System Architecture

## Kiến trúc tổng thể

```text
Client
  ├── Admin Studio
  └── Learner App
          |
       FastAPI
          |
  ┌───────┼──────────────────────────────┐
  │       │                              │
Postgres Redis                        Object Storage
  │       │                              │
  │    Celery/Temporal                    │
  │       │                              │
  │   LangGraph Research Engine          │
  │       │                              │
  │   ┌───┼──────────────┐               │
  │   │   │              │               │
  │ Search Crawl       Documents         │
  │   │   │              │               │
  │ SearXNG Crawl4AI   Docling            │
  │        Browser-use                    │
  │                                      │
  ├── pgvector
  ├── OpenSearch (phase 2)
  └── Neo4j (phase 3)
```

## Bounded contexts

1. Identity
2. Projects
3. Sources
4. Research
5. Evidence
6. Knowledge
7. Curriculum
8. Assessment
9. Learning
10. Evaluation
11. Audit

## Runtime services

### API
- CRUD.
- Auth.
- Project orchestration.
- Admin endpoints.
- Learner endpoints.
- SSE/WebSocket progress updates.

### Worker
- Search.
- Crawl.
- Document parsing.
- Embedding.
- Research workflows.
- Generation.
- Evaluation.

### Search broker
- Provider adapter.
- Query expansion.
- Deduplication.
- Result fusion.
- Domain filters.

### Model gateway
- Planner model.
- Extraction model.
- Generation model.
- Reviewer model.
- Embedding.
- Reranker.

## Dependency rule

Core domain must not import vendor SDKs directly.

Use ports/adapters:

- SearchProvider
- CrawlProvider
- BrowserProvider
- DocumentParser
- LLMProvider
- EmbeddingProvider
- RerankerProvider
- ObjectStorage
- WorkflowEngine
