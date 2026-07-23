import { describe, expect, it, vi } from "vitest";
import { ApiError, api } from "@/api/client";
describe("typed API client", () => {
  it("preserves backend error and trace ID", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "FORBIDDEN",
              message: "No access",
              details: {},
              trace_id: "trace-10",
            },
          }),
          { status: 403 },
        ),
      ),
    );
    await expect(api("/projects")).rejects.toMatchObject({
      status: 403,
      traceId: "trace-10",
    } satisfies Partial<ApiError>);
  });
  it("sends an idempotency key for mutation", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        new Response(JSON.stringify({ id: "1" }), { status: 202 }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await api("/projects/a/research-jobs", {
      method: "POST",
      body: { goal: "x" },
      idempotencyKey: "key-1",
    });
    const request = fetchMock.mock.calls[0]?.[1];
    expect(new Headers(request?.headers).get("Idempotency-Key")).toBe("key-1");
  });
});
