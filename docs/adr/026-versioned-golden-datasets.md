# ADR 026 — versioned-golden-datasets

## Decision
Phase 9 keeps deterministic, versioned evaluation policy authoritative; provider-specific evaluation is behind adapters. Published inputs and decisions are immutable/append-only, and baseline comparison requires compatible metric versions.

## Consequences
CI remains reproducible without paid models; live provider and persistence behavior requires integration verification.
