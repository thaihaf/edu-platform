# Phase 8 — Question safeguards fix

## Plan

1. Scope idempotency lookup to a project and key pair.
2. Require meaningful non-choice answers/rubrics, sanitize independent-solver requests, and add deterministic ambiguity gates.
3. Revoke approval and invalidate cached validation after negative review decisions.
4. Materialize direct evidence into immutable, fully attributed question citations.
5. Add focused regression coverage and retain Phase 8 boundaries: policy in application, contracts in domain, and in-memory adapters in infrastructure.

## Scope

This change only completes Phase 8 safeguards. It deliberately does not begin Phase 9.
