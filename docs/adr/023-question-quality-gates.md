# ADR 023 — Deterministic question quality gates

## Decision

Question origin, structure, evidence, solver isolation, ambiguity, distractors, and publication
are governed by deterministic application policy. Models may propose artifacts but cannot approve
or publish them. Published question-bank versions and citations are immutable; review and revision
history are append-only.

## Consequences

Reported questions need direct evidence and location, source-derived factual questions retain
citations, and code/SQL approval remains blocked while sandboxes are disabled.
