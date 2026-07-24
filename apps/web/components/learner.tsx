"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { FormEvent, useState } from "react";
import { config } from "@/lib/config";
import {
  demoCourse,
  demoQuestion,
  LearnerCitation,
  LearnerQuestion,
} from "@/api/learner";
import { EmptyState, SafeMarkdown, StatusBadge } from "@/components/primitives";

const nav = [
  ["Dashboard", "/learn/dashboard"],
  ["Courses", "/learn/courses"],
  ["Practice", "/learn/practice"],
  ["Exams", "/learn/exams"],
  ["Flashcards", "/learn/flashcards"],
  ["Interview", "/learn/interviews"],
  ["Progress", "/learn/progress"],
] as const;
export function LearnerShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen md:grid md:grid-cols-[14rem_1fr]">
      <aside className="border-r bg-slate-950 p-4 text-white">
        <Link className="text-lg font-bold" href="/learn">
          Learning
        </Link>
        <nav aria-label="Learner navigation" className="mt-6 space-y-1">
          {nav.map(([name, href]) => (
            <Link
              key={href}
              className={`block rounded px-3 py-2 ${path.startsWith(href) ? "bg-blue-600" : "hover:bg-slate-800"}`}
              href={href}
            >
              {name}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="mx-auto w-full max-w-6xl p-6">
        {config.mockMode ? children : <AccessRequired />}
      </main>
    </div>
  );
}
function AccessRequired() {
  return (
    <section role="alert" className="rounded border p-6">
      <h1 className="text-2xl font-bold">Learner access required</h1>
      <p className="mt-2">
        Sign in with a learner-authorized account. Development fixtures are
        available only when <code>NEXT_PUBLIC_MOCK_MODE=true</code>.
      </p>
    </section>
  );
}
function Header({ title, detail }: { title: string; detail: string }) {
  return (
    <header className="mb-6">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="text-slate-600">{detail}</p>
    </header>
  );
}
export function Dashboard() {
  return (
    <>
      <Header
        title="Your learning dashboard"
        detail="Published courses and deterministic recommendations."
      />
      <section className="grid gap-4 md:grid-cols-3">
        <Card title="Continue learning">
          <p>{demoCourse.title}</p>
          <Progress value={demoCourse.progress} />
          <Link
            className="button"
            href={`/learn/courses/${demoCourse.id}/lessons/lesson-1`}
          >
            Resume lesson
          </Link>
        </Card>
        <Card title="Weak skill">
          <p>Semantic HTML</p>
          <StatusBadge value="Needs practice" />
          <Link href="/learn/skills/semantic-html">Review skill</Link>
        </Card>
        <Card title="Recommended next step">
          <p>
            Finish “Headings and landmarks” because it is your current
            incomplete lesson.
          </p>
        </Card>
      </section>
      <section className="mt-6">
        <h2 className="text-xl font-bold">Recent learning</h2>
        <p>1 completed lesson · 1 practice session · no exam results yet.</p>
      </section>
    </>
  );
}
function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3 rounded border bg-white p-4">
      <h2 className="font-bold">{title}</h2>
      {children}
    </section>
  );
}
export function Progress({ value }: { value: number }) {
  return (
    <div>
      <div className="flex justify-between">
        <span>Progress</span>
        <span>{value}%</span>
      </div>
      <progress className="w-full" value={value} max="100">
        {value}%
      </progress>
    </div>
  );
}
export function Courses() {
  const [term, setTerm] = useState("");
  const shown = demoCourse.title.toLowerCase().includes(term.toLowerCase());
  return (
    <>
      <Header
        title="Published courses"
        detail="Only published versions available to this learner are shown."
      />
      <label>
        Search courses{" "}
        <input
          className="ml-2 border"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
      </label>
      {shown ? (
        <Card title={demoCourse.title}>
          <p>{demoCourse.description}</p>
          <p>
            {demoCourse.difficulty} · {demoCourse.duration} · Version{" "}
            {demoCourse.versionId}
          </p>
          <Progress value={demoCourse.progress} />
          <Link className="button" href={`/learn/courses/${demoCourse.id}`}>
            Continue course
          </Link>
        </Card>
      ) : (
        <EmptyState
          title="No published courses match"
          detail="Try a different search term."
        />
      )}
    </>
  );
}
export function CourseOverview() {
  return (
    <>
      <Header title={demoCourse.title} detail={demoCourse.description} />
      <Card title="Course overview">
        <p>
          Intermediate · {demoCourse.duration} · Published version{" "}
          {demoCourse.versionId}
        </p>
        <h2 className="font-bold">Learning outcomes</h2>
        <ul className="list-disc pl-5">
          <li>Use semantic document structure.</li>
          <li>Explain accessible navigation.</li>
        </ul>
        <h2 className="font-bold">Modules</h2>
        <ol className="list-decimal pl-5">
          <li>
            <Link href={`/learn/courses/${demoCourse.id}/lessons/lesson-1`}>
              HTML structure and headings
            </Link>{" "}
            — in progress
          </li>
          <li>Accessible interactions — not started</li>
        </ol>
        <Citation citation={demoQuestion.citation} />
      </Card>
    </>
  );
}
export function LessonReader() {
  const [complete, setComplete] = useState(false);
  return (
    <>
      <Header
        title="Headings and landmarks"
        detail="Module 1 · Published course version course-v1"
      />
      <div className="grid gap-5 lg:grid-cols-[14rem_1fr_16rem]">
        <nav aria-label="Lesson navigation" className="rounded border p-3">
          <p className="font-bold">Module 1</p>
          <Link href="#content">Headings and landmarks</Link>
          <p aria-current="step">{complete ? "Completed" : "In progress"}</p>
        </nav>
        <article id="content" className="space-y-4 rounded border bg-white p-5">
          <LessonBlock type="HEADING" content="Use one primary heading" />
          <LessonBlock
            type="MARKDOWN"
            content={
              "# Safe lesson content\n\nUse **semantic** headings to give readers an outline. Unsafe HTML is rendered as text."
            }
          />
          <LessonBlock
            type="CODE"
            content={"<main>\n  <h1>Course title</h1>\n</main>"}
          />
          <LessonBlock
            type="DIAGRAM_SPEC"
            content="Document outline: main → h1 → section → h2 (display-only specification)."
          />
          <LessonBlock
            type="CHECKPOINT_PLACEHOLDER"
            content="Practice checkpoint available after this lesson. Questions are not embedded in the lesson."
          />
          <button
            className="rounded bg-blue-700 px-3 py-2 text-white"
            onClick={() => setComplete(true)}
          >
            {complete ? "Lesson completed" : "Mark lesson complete"}
          </button>
          <div className="flex justify-between">
            <span>Previous lesson</span>
            <Link href="/learn/practice">Next: practice</Link>
          </div>
        </article>
        <aside>
          <Citation citation={demoQuestion.citation} />
          <h2 className="mt-4 font-bold">Objectives</h2>
          <p>Recognize semantic page headings.</p>
        </aside>
      </div>
    </>
  );
}
export function LessonBlock({
  type,
  content,
}: {
  type: string;
  content: string;
}) {
  return (
    <section>
      <h2 className="text-sm font-bold text-slate-600">
        {type.replaceAll("_", " ")}
      </h2>
      {type === "CODE" ? (
        <pre className="overflow-auto rounded bg-slate-950 p-3 text-white">
          <code>{content}</code>
        </pre>
      ) : (
        <SafeMarkdown>{content}</SafeMarkdown>
      )}
    </section>
  );
}
export function Citation({ citation }: { citation: LearnerCitation }) {
  const safe =
    citation.url && /^https?:\/\//i.test(citation.url)
      ? citation.url
      : undefined;
  return (
    <section className="rounded border p-3">
      <h2 className="font-bold">Citation: {citation.label}</h2>
      <p>
        {citation.title} · {citation.publisher} ·{" "}
        {citation.section ?? citation.sourceType}
      </p>
      {safe && (
        <a href={safe} target="_blank" rel="noopener noreferrer">
          Open {new URL(safe).hostname}
        </a>
      )}
    </section>
  );
}
function QuestionSession({ mode }: { mode: "practice" | "exam" }) {
  const [answer, setAnswer] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const q: LearnerQuestion = demoQuestion;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (answer) setSubmitted(true);
  };
  return (
    <>
      <Header
        title={mode === "exam" ? "Exam session" : "Practice session"}
        detail={`${mode === "exam" ? "Fixed published set; feedback waits for completion." : "Feedback is available after submission."} Answer 1 of 1`}
      />
      <form onSubmit={submit} className="rounded border bg-white p-5">
        <fieldset disabled={submitted}>
          <legend className="font-bold">{q.stem}</legend>
          {q.options?.map((o) => (
            <label className="mt-3 block" key={o.id}>
              <input
                required
                type="radio"
                name="answer"
                value={o.id}
                onChange={() => setAnswer(o.id)}
              />{" "}
              {o.label}
            </label>
          ))}
        </fieldset>
        {!submitted && (
          <button className="mt-4 rounded bg-blue-700 px-3 py-2 text-white">
            Submit answer
          </button>
        )}
        {submitted &&
          (mode === "practice" ? (
            <section role="status" className="mt-4 rounded bg-green-50 p-3">
              <strong>Correct.</strong> A primary heading represents the
              document’s top-level subject. <Citation citation={q.citation} />
            </section>
          ) : (
            <section role="status" className="mt-4">
              <p>
                Answer saved. Correct answers remain hidden until you submit the
                exam.
              </p>
              <Link className="button" href="/learn/results/exam-attempt-1">
                Submit exam
              </Link>
            </section>
          ))}
      </form>
    </>
  );
}
export function Practice({ session }: { session?: boolean }) {
  return session ? (
    <QuestionSession mode="practice" />
  ) : (
    <>
      <Header
        title="Practice"
        detail="Select published, approved questions only."
      />
      <Card title="Quick practice">
        <p>1 single-choice question · Semantic HTML · Intermediate</p>
        <Link className="button" href="/learn/practice/practice-session-1">
          Start practice
        </Link>
      </Card>
    </>
  );
}
export function Exams({ session }: { session?: boolean }) {
  return session ? (
    <QuestionSession mode="exam" />
  ) : (
    <>
      <Header
        title="Exams"
        detail="Fixed published question-bank versions; no proctoring."
      />
      <Card title="HTML foundations exam">
        <p>1 question · Version question-bank-v1 · Timer not configured</p>
        <Link className="button" href="/learn/exams/exam-session-1">
          Start exam
        </Link>
      </Card>
    </>
  );
}
export function Result() {
  return (
    <>
      <Header
        title="Exam result"
        detail="Published question-bank version question-bank-v1"
      />
      <Card title="Score">
        <p className="text-3xl font-bold">100%</p>
        <p>1 correct · 0 incorrect · 0 unanswered</p>
        <p>Semantic HTML: Strong · Bloom level: Remember</p>
        <Link href="/learn/skills/semantic-html">
          View skill recommendation
        </Link>
      </Card>
    </>
  );
}
export function Flashcards({ deck }: { deck?: boolean }) {
  const [revealed, setRevealed] = useState(false);
  const [status, setStatus] = useState("NEW");
  return (
    <>
      <Header
        title={deck ? "HTML foundations cards" : "Flashcards"}
        detail="Basic deterministic review policy: New, Review, Mastered."
      />
      {deck ? (
        <Card title={`Card 1 · ${status}`}>
          <p className="text-xl">What does an h1 communicate?</p>
          {revealed && (
            <p role="status">The primary subject of the document or section.</p>
          )}
          <button className="button" onClick={() => setRevealed(true)}>
            {revealed ? "Answer revealed" : "Reveal answer"}
          </button>
          {revealed && (
            <div className="mt-3 flex gap-2">
              <button onClick={() => setStatus("REVIEW")}>Again</button>
              <button onClick={() => setStatus("MASTERED")}>Understood</button>
            </div>
          )}
          <Citation citation={demoQuestion.citation} />
        </Card>
      ) : (
        <Card title="HTML foundations cards">
          <p>3 cards · 1 new · 2 review</p>
          <Link className="button" href="/learn/flashcards/html-foundations">
            Open deck
          </Link>
        </Card>
      )}
    </>
  );
}
export function Interview({ session }: { session?: boolean }) {
  const [submitted, setSubmitted] = useState(false);
  return (
    <>
      <Header
        title={session ? "Text mock interview" : "Mock interviews"}
        detail="Text only. Feedback is rubric-based and may be model-assisted."
      />
      {session ? (
        <Card title="Question 1 of 1">
          <p>
            Explain how you would structure a page for assistive technology.
          </p>
          <textarea
            aria-label="Interview response"
            className="mt-3 block w-full border"
            rows={5}
            disabled={submitted}
          />
          {!submitted ? (
            <button className="button mt-3" onClick={() => setSubmitted(true)}>
              Submit response
            </button>
          ) : (
            <section role="status" className="mt-3 rounded bg-slate-50 p-3">
              <strong>Provisional rubric feedback</strong>
              <p>
                Strength: identified semantic landmarks. Missing point: explain
                heading order. This feedback is guidance, not absolute truth.
              </p>
              <StatusBadge value="Human-authored question" />
            </section>
          )}
        </Card>
      ) : (
        <Card title="Semantic HTML interview">
          <p>
            1 approved interview question · Published version question-bank-v1
          </p>
          <Link className="button" href="/learn/interviews/interview-session-1">
            Start text interview
          </Link>
        </Card>
      )}
    </>
  );
}
export function SkillProgress() {
  const params = useParams<{ skillId?: string }>();
  return (
    <>
      <Header
        title={params.skillId ? "Semantic HTML" : "Learning progress"}
        detail="Deterministic summaries from completed attempts; not psychometric mastery."
      />
      <Card title="Semantic HTML">
        <StatusBadge value="Needs practice" />
        <p>
          Practice accuracy: 50% · Recent attempts: 2 · Policy:
          simple-skill-summary-v1
        </p>
        <p>
          Recommendation: review headings and landmarks because this skill was
          recently missed.
        </p>
        <Link href={`/learn/courses/${demoCourse.id}/lessons/lesson-1`}>
          Study linked lesson
        </Link>
      </Card>
    </>
  );
}
