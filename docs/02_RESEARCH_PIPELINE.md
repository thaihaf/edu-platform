# Deep Research Pipeline

## State machine

```text
CREATED
→ SCOPING
→ PLANNING
→ DISCOVERING
→ FETCHING
→ PARSING
→ EXTRACTING
→ CONSOLIDATING
→ GAP_ANALYSIS
→ FOLLOWUP_RESEARCH
→ KNOWLEDGE_BUILDING
→ COURSE_GENERATION
→ QUESTION_GENERATION
→ EVALUATING
→ REVIEW_REQUIRED
→ READY_TO_PUBLISH
→ PUBLISHED
```

## Research loop

1. Parse user goal.
2. Generate research brief.
3. Build entity aliases.
4. Generate query families.
5. Execute multi-provider search.
6. Fetch accessible sources.
7. Normalize documents.
8. Extract claims, questions, skills and metadata.
9. Detect copied/duplicate sources.
10. Build evidence graph.
11. Identify conflicts.
12. Identify knowledge gaps.
13. Run follow-up searches.
14. Stop when:
   - research budget reached,
   - coverage threshold met,
   - marginal information gain is low.

## Query families

- Direct.
- Candidate language.
- File type.
- Site-specific.
- Phrase fingerprint.
- Historical/year-specific.
- Entity alias.
- Contradiction.
- Citation chasing.
- Related organizations.
- Technology-specific.
- Domain-specific.

## Search output contract

Each search result must include:

- provider
- query
- rank
- title
- url
- snippet
- published_at if known
- discovered_at
- content_type
- access_status
- relevance_score
- source_type_guess

## Research quality metrics

- Source diversity.
- Official source coverage.
- Candidate report coverage.
- Temporal coverage.
- Query family coverage.
- Claim corroboration.
- Contradiction resolution.
- Source independence.
- Citation completeness.

## Phase 4 discovery and fetch boundary
Phase 4 accepts explicit query families and query strings only. Providers are fused with
reciprocal-rank fusion (RRF, k=60), with provider rank and provenance retained on each
canonical-URL duplicate cluster. Public URL fetches are subject to DNS-based SSRF checks,
robots policy, byte/type/redirect limits and normalized immutable snapshots. AI planning,
claim extraction, and research loops remain later phases.

## Phase 5 orchestration boundary
Phase 5 introduces a versioned, serializable research-job state. Checkpoints contain IDs and
structured planning metadata—not fetched bodies—and are saved after meaningful nodes. Budgets,
cancellation, and follow-up stopping policy are deterministic application concerns; a model may
recommend work but cannot override those limits. Candidate observations remain unverified until
Phase 6 evidence processing.
