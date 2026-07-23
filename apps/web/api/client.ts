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
