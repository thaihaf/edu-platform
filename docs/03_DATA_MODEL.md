# Data Model

## Core entities

### Workspace
Multi-tenant boundary.

### ResearchProject
Represents one goal such as "Agribank CNTT-02".

Fields:
- id
- workspace_id
- title
- description
- domain
- target
- locale
- status
- research_depth
- created_by
- created_at
- updated_at

### Source
- id
- canonical_url
- source_type
- title
- publisher
- author
- published_at
- fetched_at
- language
- access_status
- authority_score
- directness_score
- freshness_score
- commercial_bias_score
- independence_cluster_id
- content_hash
- metadata_json

### SourceSnapshot
Immutable fetched content.

### SourceChunk
- source_snapshot_id
- page
- section_path
- text
- embedding
- token_count
- chunk_hash

### Claim
- statement
- category
- valid_from
- valid_to
- confidence
- status

### EvidenceLink
- claim_id
- source_chunk_id
- relation: supports|contradicts|mentions|derived_from
- directness
- strength
- reviewer_status

### Skill
- name
- description
- parent_skill_id
- prerequisites
- taxonomy_path

### ReportedQuestion
- text
- normalized_text
- origin_type
- appeared_year
- appeared_round
- organization
- role
- confidence_appeared
- answer_status
- source_links

### Course
### CourseVersion
### Module
### Lesson
### ContentBlock
### LearningObjective

### Question
- type
- stem
- answer
- explanation
- difficulty
- bloom_level
- origin_type
- confidence
- review_status
- prompt_version
- model
- source_set_hash

### GenerationJob
### EvaluationRun
### AuditEvent
### UserProgress

## Origin types

- VERBATIM_REPORTED
- PARAPHRASED_REPORTED
- SOURCE_DERIVED
- JD_INFERRED
- DOMAIN_STANDARD
- AI_SYNTHESIZED

## Versioning

A published CourseVersion is immutable.
Updates create a new DRAFT CourseVersion.
