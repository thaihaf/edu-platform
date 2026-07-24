# UI Specification

## Admin Studio

Navigation:
- Projects
- Sources
- Research
- Evidence
- Knowledge Map
- Curriculum
- Lessons
- Question Bank
- Review Queue
- Versions
- Evaluation
- Settings

## Project creation wizard

Step 1: Goal
Step 2: Initial sources
Step 3: Research policy
Step 4: Assessment types
Step 5: Cost/depth limits
Step 6: Start

## Research dashboard

Must show:
- current phase
- queries issued
- sources discovered/fetched/rejected
- source categories
- evidence count
- unresolved conflicts
- gaps
- token/cost usage
- activity timeline

## Source viewer

Three panels:
- original snapshot
- normalized text
- extracted claims/questions

## Question review

Display:
- question
- answer
- explanation
- origin type
- evidence
- independent solver result
- ambiguity result
- duplicate candidates
- model/prompt
- approve/edit/reject

## Learner experience

- Study dashboard
- Lesson reader
- Source citations
- Practice mode
- Exam mode
- Flashcards
- Mock interview
- Weak-skill analytics

## Phase 10 administrative studio

The desktop-first administrative studio has a persistent sidebar for Dashboard, Projects, Sources,
Research, Evidence, Knowledge, Courses, Question Banks, Evaluation, and Settings. Its header
contains workspace/project selection, breadcrumbs, command-palette placeholder, environment,
health, deferred-verification, and current-user indicators. Every API-backed panel must provide
loading, empty, denied, not-found, and safe retry states; error details expose backend code and
trace ID without a stack trace.

All mutations use backend contracts and idempotency keys where applicable. Published course,
question-bank, dataset, and policy versions are visibly read-only. Source and Markdown content is
rendered as text/sanitized Markdown only; untrusted HTML is never injected. Forms have labels,
error summaries, keyboard focus, confirmation for state-changing actions, and textual status in
addition to visual styling. The phase scaffold provides the shell and primary context pages; live
endpoint completeness is deferred until the API exposes list/detail contracts consistently.

## Phase 10B research and evidence administration

Phase 10B adds project detail plus project-scoped Sources, Research, Claims, Source Clusters,
Reported Questions, Skills, and Knowledge Gaps routes. The implemented source text-ingestion,
research control, and claim-review panels use typed FastAPI contracts, preserve structured error
trace IDs, prevent duplicate submissions, and use confirmation before lifecycle/review mutations.
Research polling stops on terminal statuses. Where the backend lacks a paginated list/detail
contract, the route visibly reports that the feature is unavailable rather than showing invented
records. Tables retain semantic headers and responsive overflow; source content is rendered as
safe text. Severity, status, and lineage caution use written labels, not color alone.

## Phase 10C course, question, and evaluation administration

Phase 10C adds project-scoped course and question-generation forms plus supported generation-job
inspection. They use typed asynchronous FastAPI contracts, idempotency keys, textual statuses, and
bounded polling that stops at terminal states or while the document is hidden. The course and
question-bank/evaluation routes required by the admin information architecture are present. When
FastAPI does not expose a documented contract, a route presents an accessible availability notice
with the exact required endpoint instead of mocked records, fake publication success, or browser
policy.

Course-editor, question-review, versioning, validation/publication, datasets, policies, baselines,
and evaluation-results pages retain their required safe design: published versions are immutable;
content blocks, JSON, code, and diagram specifications are treated as text; confidence, origin,
and gate values have written labels; citations must not expose storage URLs; and destructive
transitions require backend-supported confirmation. The missing endpoints are listed in the Phase
10C note and frontend API limitations.

### Accessibility and security notes

Generation forms have associated labels, visible error summaries, disabled duplicate submits, and
recoverable input retention. Job events use semantic headings and textual status. Untrusted text is
not inserted as HTML; JSON validation parses but never evaluates values. External citation
navigation will be limited to safe links with `rel="noopener noreferrer"` once citation records are
available. No provider credentials, raw prompts, storage paths, or hidden answer metadata are
placed in browser state.

## Phase 11 learner UI

`/learn` has a learner-only shell with course, practice, exam, flashcard, interview, and progress
navigation. Lesson readers preserve heading hierarchy, render unsafe content as text, provide
completion/navigation controls, and expose safe citations. Controls use semantic labels, visible
focus, native progress/form controls, status announcements, and reduced-motion styling.
