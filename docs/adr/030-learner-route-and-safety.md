# ADR 030: Separate learner routes and learner-safe contracts

Learner UI uses the existing Next.js application under `(learner)/learn`; it does not reuse the
admin shell or admin data cache. Learner contracts are separate and omit answer keys before
submission, reviewer data, prompts, raw evidence identifiers, and credentials. Published content,
ownership, scoring, and publication remain backend authority.
