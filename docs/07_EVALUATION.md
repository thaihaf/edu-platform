# Evaluation Plan

## Research metrics

- source_relevance
- source_diversity
- source_authority
- temporal_coverage
- evidence_directness
- corroboration
- contradiction_handling
- citation_correctness
- claim_groundedness
- research_completeness

## Course metrics

- objective_coverage
- prerequisite_consistency
- lesson_coherence
- source_coverage
- redundancy
- difficulty_progression
- domain_alignment

## Question metrics

- factual_correctness
- single_best_answer
- distractor_quality
- ambiguity
- bloom_alignment
- difficulty
- grounding
- duplicate_similarity
- language_quality

## Quality gates

A question cannot be published when:

- no answer,
- unsupported factual answer,
- unresolved reviewer disagreement,
- similarity > 0.92 with an existing question unless marked duplicate,
- origin type reported without evidence,
- citation missing for source-derived claims.

## Golden datasets

Create:
- `evals/agribank/research_cases.jsonl`
- `evals/agribank/questions.jsonl`
- `evals/general/course_generation.jsonl`

Each case includes:
- input
- expected facts
- required sources
- forbidden claims
- rubric

## Phase 6 quality gates
Evaluate claim fingerprint stability, independence-aware corroboration, contradiction scope matching,
direct reported-question provenance, confidence component reproducibility, review auditability, and
acyclic skill relationships.

## Phase 7 quality gates
A draft must have cited factual blocks, objectives for every lesson, resolvable prerequisites, unique
positions, approved claim/skill linkage, and no executable content before publication.

## Phase 9 platform policy
Metric name, version and configuration hash identify a result. Deterministic validators own hard safety
gates; optional DeepEval/model judges are advisory. Golden datasets, policies, baselines and append-only
results make regression decisions reproducible and CI runs use deterministic fixtures only.

## Phase 11 learner feedback

Objective answers are evaluated only after submission. Essay/interview feedback is explicitly
provisional/model-assisted where applicable. Exam review waits until terminal submission. Skill
labels use a versioned deterministic policy and do not assert validated psychometric mastery.
