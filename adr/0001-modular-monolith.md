# ADR 0001 — Modular Monolith for MVP

Status: Accepted

Decision:
Use a modular monolith with API and worker processes sharing domain packages.

Reason:
- Faster delivery.
- Easier transactions.
- Lower operational cost.
- Clear future extraction boundaries.
- Research workloads remain separate as jobs without requiring microservices.
