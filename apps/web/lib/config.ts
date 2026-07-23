export const config = {
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  authMode: process.env.NEXT_PUBLIC_AUTH_MODE ?? "mock",
  mockMode: process.env.NEXT_PUBLIC_MOCK_MODE === "true",
  pollingMs: Number(process.env.NEXT_PUBLIC_POLLING_INTERVAL_MS ?? 5000),
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT_LABEL ?? "local",
} as const;
