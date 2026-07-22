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
