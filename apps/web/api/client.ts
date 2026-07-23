import { config } from "@/lib/config";
export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    trace_id: string;
  };
};
export class ApiError extends Error {
  constructor(
    public readonly body: ApiErrorBody,
    public readonly status: number,
  ) {
    super(body.error.message);
  }
  get traceId() {
    return this.body.error.trace_id;
  }
}
export type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  idempotencyKey?: string;
  signal?: AbortSignal;
  token?: string;
  query?: Record<string, string | number | boolean | undefined>;
  retry?: boolean;
};
export type Project = {
  id: string;
  title: string;
  description: string;
  domain: string;
  target: string;
  locale: string;
  research_depth: number;
  status: string;
  updated_at: string;
};
export type Source = {
  id: string;
  project_id: string;
  source_type: string;
  title: string;
  canonical_url?: string | null;
  publisher?: string | null;
  updated_at: string;
};
export type IngestionJob = {
  id: string;
  status: string;
  stage: string;
  progress_percent: number;
  error_code?: string | null;
  error_message?: string | null;
};
export type ResearchJob = {
  id: string;
  project_id: string;
  status: string;
  current_phase: string;
  progress_percent: number;
  followup_round: number;
  budgets: {
    queries_used: number;
    query_budget: number;
    sources_selected: number;
    source_budget: number;
    model_calls_used: number;
    model_call_budget: number;
  };
  stop_reason?: string | null;
  created_at: string;
  completed_at?: string | null;
};
export type Claim = {
  id: string;
  project_id: string;
  normalized_statement: string;
  claim_type: string;
  status: string;
  review_status: string;
  confidence: number;
  confidence_components: Record<string, number>;
  temporal_scope: Record<string, unknown>;
  updated_at: string;
};
export type ReviewDecision =
  | "APPROVE"
  | "REJECT"
  | "REQUEST_CHANGES"
  | "MARK_DISPUTED"
  | "MARK_OBSOLETE";
export const apiPaths = {
  project: (id: string) => `/projects/${id}`,
  sources: (id: string) => `/projects/${id}/sources`,
  source: (id: string) => `/sources/${id}`,
  research: (id: string) => `/research-jobs/${id}`,
  claims: (id: string) => `/projects/${id}/claims`,
  claim: (id: string) => `/claims/${id}`,
} as const;
export const idempotencyKey = () => crypto.randomUUID();
export async function api<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const url = new URL(`${config.apiBaseUrl}${path}`);
  Object.entries(options.query ?? {}).forEach(
    ([k, v]) => v !== undefined && url.searchParams.set(k, String(v)),
  );
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 15000);
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Trace-ID": crypto.randomUUID(),
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.idempotencyKey)
    headers["Idempotency-Key"] = options.idempotencyKey;
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  try {
    const response = await fetch(url, {
      method: options.method ?? "GET",
      headers,
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal ?? controller.signal,
    });
    if (!response.ok) {
      let body: ApiErrorBody;
      try {
        body = await response.json();
      } catch {
        body = {
          error: {
            code: "NETWORK_ERROR",
            message: "The API returned an unreadable error.",
            details: {},
            trace_id: response.headers.get("X-Trace-ID") ?? "",
          },
        };
      }
      throw new ApiError(body, response.status);
    }
    return response.status === 204
      ? (undefined as T)
      : (response.json() as Promise<T>);
  } finally {
    window.clearTimeout(timer);
  }
}

export type CourseGenerationJob = {
  id: string;
  project_id: string;
  course_id?: string | null;
  status: string;
  current_stage: string;
  progress_percent: number;
  target_outcome: string;
  target_audience: string;
  learner_profile?: string | null;
  locale: string;
  time_budget?: number | null;
  module_limit?: number | null;
  lesson_limit?: number | null;
  policy_version: string;
  prompt_version: string;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};
export type QuestionGenerationJob = {
  id: string;
  project_id: string;
  status: string;
  current_stage: string;
  progress_percent: number;
  requested_question_types: string[];
  requested_count: number;
  generated_count: number;
  accepted_count: number;
  rejected_count: number;
  model_calls_used: number;
  tokens_used?: number | null;
  estimated_cost?: number | null;
  policy_version: string;
  prompt_version: string;
  error_code?: string | null;
  error_message?: string | null;
};
export type JobEvent = {
  id?: string;
  type?: string;
  stage?: string;
  message?: string;
  created_at?: string;
};
export const phase10cPaths = {
  courseGeneration: (projectId: string) =>
    `/projects/${projectId}/course-generation-jobs`,
  courseGenerationJob: (jobId: string) => `/course-generation-jobs/${jobId}`,
  courseGenerationEvents: (jobId: string) =>
    `/course-generation-jobs/${jobId}/events`,
  questionGeneration: (projectId: string) =>
    `/projects/${projectId}/question-generation-jobs`,
  questionGenerationJob: (jobId: string) =>
    `/question-generation-jobs/${jobId}`,
  questionGenerationEvents: (jobId: string) =>
    `/question-generation-jobs/${jobId}/events`,
} as const;
