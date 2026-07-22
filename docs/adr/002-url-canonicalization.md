# ADR: 002 url canonicalization

## Decision
Phase 4 uses deterministic, provider-neutral policy: RRF keeps provenance; canonical URLs
remove fragments/default ports and configured tracking keys without reordering meaningful
queries; robots retrieval failures deny access; duplicate/near-duplicate grouping preserves
all sources and reports lineage confidence; browser access is disabled by default.

## Consequences
These choices favor auditable discovery and safe public access over recall. Canonicalization
is not proof that URLs are semantically identical, and lineage is never presented as certain
without strong evidence.
