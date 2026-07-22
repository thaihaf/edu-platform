# AI Workflows

## Workflow: create_course

Inputs:
- project_id
- goal
- initial_sources
- research_policy
- assessment_policy

Steps:
1. goal_understanding
2. research_brief_generation
3. query_plan_generation
4. source_discovery
5. content_fetch
6. content_parse
7. evidence_extraction
8. source_deduplication
9. evidence_consolidation
10. gap_analysis
11. followup_research
12. skill_graph_generation
13. curriculum_generation
14. lesson_generation
15. question_mining
16. question_generation
17. question_validation
18. course_evaluation
19. human_review

## Workflow: update_course

Inputs:
- published_course_version
- new_sources or new goal constraints

Outputs:
- affected modules
- added claims
- changed claims
- obsolete claims
- questions to add
- questions to revise
- draft course diff

## Workflow: validate_question

1. Grounding check.
2. Independent solve.
3. Distractor check.
4. Ambiguity check.
5. Difficulty estimate.
6. Duplicate detection.
7. Domain correctness.
8. Citation check.

## Phase 5 workflow policy
The LangGraph adapter is behind a framework-independent workflow port. Nodes use versioned
structured prompts and treat delimited source material as untrusted data; source text cannot invoke
tools, reveal secrets, import code, change policy, or promote itself to trusted status.
