"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  api,
  CourseGenerationJob,
  idempotencyKey,
  JobEvent,
  phase10cPaths,
  QuestionGenerationJob,
} from "@/api/client";
import { mockUser } from "@/lib/auth";
import {
  ErrorState,
  LoadingSkeleton,
  SafeMarkdown,
  StatusBadge,
} from "@/components/primitives";
import { Unavailable } from "@/components/admin-data";

const terminal = new Set(["COMPLETED", "FAILED", "CANCELLED"]);
const courseSchema = z.object({
  target_outcome: z.string().min(1, "Target outcome is required"),
  target_audience: z.string().min(1, "Target audience is required"),
  learner_profile: z.string(),
  course_id: z.string(),
  locale: z.string().min(2),
  time_budget: z.coerce.number().int().positive().optional(),
  module_limit: z.coerce.number().int().positive().optional(),
  lesson_limit: z.coerce.number().int().positive().optional(),
});
const questionSchema = z.object({
  requested_question_types: z
    .string()
    .min(1, "Select at least one question type"),
  requested_count: z.coerce.number().int().min(1),
  difficulty_distribution: z.string(),
  bloom_distribution: z.string(),
  origin_policy: z.string(),
  course_id: z.string(),
  course_version_id: z.string(),
  module_id: z.string(),
  lesson_id: z.string(),
});
type CourseValues = z.infer<typeof courseSchema>;
type QuestionValues = z.infer<typeof questionSchema>;

export function ConfidenceBadge({ value }: { value: string }) {
  return <StatusBadge value={`Confidence: ${value}`} />;
}
export function QuestionOriginBadge({ value }: { value: string }) {
  return <StatusBadge value={`Origin: ${value}`} />;
}
export function QualityGateStatus({ value }: { value: string }) {
  return <StatusBadge value={`Quality gate: ${value}`} />;
}
export function RegressionDelta({
  value,
}: {
  value: number;
  compatible?: boolean;
}) {
  return (
    <span
      aria-label={
        value === 0
          ? "No metric change"
          : value > 0
            ? "Metric improvement"
            : "Metric regression"
      }
    >
      {value > 0 ? "▲" : value < 0 ? "▼" : "•"}{" "}
      {compatible === false
        ? "Incompatible metric version"
        : `${value >= 0 ? "+" : ""}${value.toFixed(2)}`}
    </span>
  );
}
export function JsonEditor({
  label,
  value,
  onChange,
  readOnly = false,
}: {
  label: string;
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
}) {
  let invalid = false;
  try {
    JSON.parse(value || "{}");
  } catch {
    invalid = true;
  }
  return (
    <label className="block">
      {label}
      <textarea
        aria-invalid={invalid}
        aria-describedby={`${label}-error`}
        className="mt-1 block min-h-24 w-full border font-mono"
        value={value}
        readOnly={readOnly}
        onChange={(e) => onChange?.(e.target.value)}
      />
      {invalid && (
        <span id={`${label}-error`} role="alert">
          Enter valid JSON; content is treated as text and never executed.
        </span>
      )}
    </label>
  );
}
export function ImmutableVersionControls({ status }: { status: string }) {
  return status === "PUBLISHED" ? (
    <p role="status">
      🔒 Published versions are immutable. Create a new draft based on this
      version to make changes.
    </p>
  ) : (
    <div className="flex gap-2">
      <button className="rounded border px-3 py-2">Validate with API</button>
      <button className="rounded border px-3 py-2">
        Publish after valid API result
      </button>
    </div>
  );
}
export function CitationPanel() {
  return (
    <section className="rounded border p-4">
      <h2 className="font-bold">Citations and evidence</h2>
      <p>
        Citation data is unavailable until the course-version citation read
        contract is exposed. This panel will show claim, evidence relation,
        source, snapshot, chunks, page, section, extracted span, and citation
        type. External source links will use safe navigation only.
      </p>
    </section>
  );
}
export function ProtectedContentBlock({
  blockType = "PARAGRAPH",
  content = "",
}: {
  blockType?: string;
  content?: string;
}) {
  return (
    <article className="rounded border p-3">
      <header className="flex justify-between">
        <StatusBadge value={`Block: ${blockType}`} />
        <span>🔒 Human-authored lock</span>
      </header>
      <SafeMarkdown>{content}</SafeMarkdown>
      <p className="text-sm">
        Structured content is rendered as text; code and diagram specifications
        are never executed.
      </p>
    </article>
  );
}

export function CourseGenerationForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const form = useForm<CourseValues>({
    resolver: zodResolver(courseSchema),
    defaultValues: { locale: "en", learner_profile: "", course_id: "" },
  });
  const mutation = useMutation({
    mutationFn: (values: CourseValues) =>
      api<CourseGenerationJob>(phase10cPaths.courseGeneration(projectId), {
        method: "POST",
        idempotencyKey: idempotencyKey(),
        body: {
          ...values,
          course_id: values.course_id || undefined,
          created_by: mockUser.id,
        },
      }),
    onSuccess: (job) => router.push(`/course-generation-jobs/${job.id}`),
  });
  return (
    <form
      className="space-y-3 rounded border bg-white p-5"
      onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
    >
      <h2 className="text-xl font-bold">Generate course draft</h2>
      <p>
        Generation is asynchronous (202). Budget and policy limits are enforced
        by FastAPI.
      </p>
      <label className="block">
        Target outcome
        <input
          className="block w-full border"
          {...form.register("target_outcome")}
        />
      </label>
      <label className="block">
        Target audience
        <input
          className="block w-full border"
          {...form.register("target_audience")}
        />
      </label>
      <label className="block">
        Existing course ID (optional)
        <input
          className="block w-full border"
          {...form.register("course_id")}
        />
      </label>
      <label className="block">
        Learner profile
        <textarea
          className="block w-full border"
          {...form.register("learner_profile")}
        />
      </label>
      <div className="grid gap-3 sm:grid-cols-4">
        <label>
          Locale
          <input className="block w-full border" {...form.register("locale")} />
        </label>
        <label>
          Minutes
          <input
            type="number"
            className="block w-full border"
            {...form.register("time_budget")}
          />
        </label>
        <label>
          Modules
          <input
            type="number"
            className="block w-full border"
            {...form.register("module_limit")}
          />
        </label>
        <label>
          Lessons
          <input
            type="number"
            className="block w-full border"
            {...form.register("lesson_limit")}
          />
        </label>
      </div>
      {Object.values(form.formState.errors).length > 0 && (
        <p role="alert">
          Correct the highlighted generation fields before submitting.
        </p>
      )}
      {mutation.isError && <ErrorState error={mutation.error} />}
      <button
        disabled={mutation.isPending}
        className="rounded bg-blue-700 px-3 py-2 text-white"
      >
        {mutation.isPending ? "Starting…" : "Start generation"}
      </button>
    </form>
  );
}
export function QuestionGenerationForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const form = useForm<QuestionValues>({
    resolver: zodResolver(questionSchema),
    defaultValues: {
      requested_question_types: "MULTIPLE_CHOICE",
      requested_count: 5,
      difficulty_distribution: "{}",
      bloom_distribution: "{}",
      origin_policy: "{}",
      course_id: "",
      course_version_id: "",
      module_id: "",
      lesson_id: "",
    },
  });
  const mutation = useMutation({
    mutationFn: (v: QuestionValues) =>
      api<QuestionGenerationJob>(phase10cPaths.questionGeneration(projectId), {
        method: "POST",
        idempotencyKey: idempotencyKey(),
        body: {
          created_by: mockUser.id,
          requested_question_types: v.requested_question_types
            .split(",")
            .map((x) => x.trim()),
          requested_count: v.requested_count,
          difficulty_distribution: JSON.parse(
            v.difficulty_distribution || "{}",
          ),
          bloom_distribution: JSON.parse(v.bloom_distribution || "{}"),
          origin_policy: JSON.parse(v.origin_policy || "{}"),
          course_id: v.course_id || undefined,
          course_version_id: v.course_version_id || undefined,
          module_id: v.module_id || undefined,
          lesson_id: v.lesson_id || undefined,
        },
      }),
    onSuccess: (job) => router.push(`/question-generation-jobs/${job.id}`),
  });
  return (
    <form
      className="space-y-3 rounded border bg-white p-5"
      onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
    >
      <h2 className="text-xl font-bold">Generate question bank draft</h2>
      <p>
        Requests are accepted asynchronously (202); no questions are fabricated
        in the browser.
      </p>
      <label className="block">
        Question types (comma-separated)
        <input
          className="block w-full border"
          {...form.register("requested_question_types")}
        />
      </label>
      <label className="block">
        Requested count
        <input
          type="number"
          className="block w-full border"
          {...form.register("requested_count")}
        />
      </label>
      <label className="block">
        Course ID (optional)
        <input
          className="block w-full border"
          {...form.register("course_id")}
        />
      </label>
      <label className="block">
        Course version ID (optional)
        <input
          className="block w-full border"
          {...form.register("course_version_id")}
        />
      </label>
      <label className="block">
        Module ID (optional)
        <input
          className="block w-full border"
          {...form.register("module_id")}
        />
      </label>
      <label className="block">
        Lesson ID (optional)
        <input
          className="block w-full border"
          {...form.register("lesson_id")}
        />
      </label>
      <JsonEditor
        label="Difficulty distribution JSON"
        value={form.watch("difficulty_distribution")}
        onChange={(v) => form.setValue("difficulty_distribution", v)}
      />
      <JsonEditor
        label="Bloom distribution JSON"
        value={form.watch("bloom_distribution")}
        onChange={(v) => form.setValue("bloom_distribution", v)}
      />
      <JsonEditor
        label="Origin policy JSON"
        value={form.watch("origin_policy")}
        onChange={(v) => form.setValue("origin_policy", v)}
      />
      {mutation.isError && <ErrorState error={mutation.error} />}
      <button
        disabled={mutation.isPending}
        className="rounded bg-blue-700 px-3 py-2 text-white"
      >
        {mutation.isPending ? "Starting…" : "Start question generation"}
      </button>
    </form>
  );
}
function Events({ events }: { events?: JobEvent[] }) {
  return (
    <section>
      <h2 className="font-bold">Events</h2>
      {events?.length ? (
        <ul>
          {events.map((e, i) => (
            <li key={e.id ?? i}>
              {e.created_at ?? ""} {e.stage ?? e.type ?? "Event"}:{" "}
              {e.message ?? "No detail"}
            </li>
          ))}
        </ul>
      ) : (
        <p>No events were returned.</p>
      )}
    </section>
  );
}
export function CourseGenerationDetail({ jobId }: { jobId: string }) {
  const q = useQuery({
    queryKey: ["course-generation-job", jobId],
    queryFn: () =>
      api<CourseGenerationJob>(phase10cPaths.courseGenerationJob(jobId)),
    refetchInterval: (query) =>
      terminal.has(query.state.data?.status ?? "") || document.hidden
        ? false
        : 3000,
  });
  const e = useQuery({
    queryKey: ["course-generation-events", jobId],
    queryFn: () => api<JobEvent[]>(phase10cPaths.courseGenerationEvents(jobId)),
    enabled: Boolean(q.data),
    refetchInterval:
      terminal.has(q.data?.status ?? "") || document.hidden ? false : 5000,
  });
  if (q.isLoading) return <LoadingSkeleton />;
  if (q.isError)
    return <ErrorState error={q.error} retry={() => q.refetch()} />;
  const j = q.data;
  return (
    <section className="space-y-4 rounded border bg-white p-5">
      <h2 className="text-xl font-bold">Course generation job</h2>
      <StatusBadge value={j.status} />
      <p>
        Stage: {j.current_stage}; progress: {j.progress_percent}%.
      </p>
      <p>
        Outcome: {j.target_outcome}; audience: {j.target_audience}; locale:{" "}
        {j.locale}.
      </p>
      <p>
        Policy: {j.policy_version}; prompt version: {j.prompt_version}.
        Model/token budget details are not returned by this API contract.
      </p>
      {j.error_message && (
        <ErrorState error={new Error(`${j.error_code}: ${j.error_message}`)} />
      )}
      <Events events={e.data} />
      {j.course_id ? (
        <Link className="underline" href={`/courses/${j.course_id}`}>
          Open generated draft
        </Link>
      ) : (
        <p>Draft navigation appears only when the API returns a course ID.</p>
      )}
    </section>
  );
}
export function QuestionGenerationDetail({ jobId }: { jobId: string }) {
  const q = useQuery({
    queryKey: ["question-generation-job", jobId],
    queryFn: () =>
      api<QuestionGenerationJob>(phase10cPaths.questionGenerationJob(jobId)),
    refetchInterval: (query) =>
      terminal.has(query.state.data?.status ?? "") || document.hidden
        ? false
        : 3000,
  });
  const e = useQuery({
    queryKey: ["question-generation-events", jobId],
    queryFn: () =>
      api<JobEvent[]>(phase10cPaths.questionGenerationEvents(jobId)),
    enabled: Boolean(q.data),
    refetchInterval:
      terminal.has(q.data?.status ?? "") || document.hidden ? false : 5000,
  });
  if (q.isLoading) return <LoadingSkeleton />;
  if (q.isError)
    return <ErrorState error={q.error} retry={() => q.refetch()} />;
  const j = q.data;
  return (
    <section className="space-y-4 rounded border bg-white p-5">
      <h2 className="text-xl font-bold">Question generation job</h2>
      <StatusBadge value={j.status} />
      <p>
        Stage: {j.current_stage}; progress: {j.progress_percent}%.
      </p>
      <p>
        Requested: {j.requested_count}; generated: {j.generated_count};
        accepted: {j.accepted_count}; rejected: {j.rejected_count}.
      </p>
      <p>
        Types: {j.requested_question_types.join(", ")}. Model calls:{" "}
        {j.model_calls_used}; tokens: {j.tokens_used ?? "not reported"}.
      </p>
      {j.error_message && (
        <ErrorState error={new Error(`${j.error_code}: ${j.error_message}`)} />
      )}
      <Events events={e.data} />
    </section>
  );
}
export function Phase10CUnavailable({
  feature,
  endpoint,
}: {
  feature: string;
  endpoint: string;
}) {
  return <Unavailable feature={feature} endpoint={endpoint} />;
}
