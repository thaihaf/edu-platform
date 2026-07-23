# ADR 0010 — Admin web stack

## Decision

Use **Next.js App Router**, React, strict TypeScript, Tailwind CSS, TanStack Query, React Hook
Form, Zod, Vitest/Testing Library, MSW, and Playwright in `apps/web`.

Routes render the stable application frame on the server and hydrate data-dependent panels as
client components. The browser uses one manually typed API client derived from the documented
FastAPI contracts; it owns transport concerns only (trace IDs, cancellation, safe retries, and
structured errors), not domain policy. TanStack Query owns server cache state, while React Hook
Form/Zod owns local form state and validation.

Authentication is an adapter boundary: an in-memory development identity is available in mock
mode, while bearer/session adapters obtain credentials from the host application rather than
persisting them in browser storage. Route/control role checks improve usability for ADMIN,
RESEARCHER, REVIEWER, EDITOR, and VIEWER but FastAPI remains authoritative.

The component layer uses semantic Tailwind primitives rather than a dependency-heavy generated
component kit. Dialogs, labels, focus rings, keyboard controls, status text, and reduced-motion
styles are part of the primitives; additional Radix components can be adopted behind the same
interfaces when the package registry is available.

Vitest/MSW cover transport and UI policy, and Playwright runs deterministic mocked journeys.
This fits the existing FastAPI modular monolith: it preserves the API as the single source of
truth, works against its existing error/trace contract, and does not replace backend services.

## Consequences

The frontend remains deployable independently and standard CI can use mock mode. Live identity,
uploads, SSE, and production deployment require the real infrastructure and are explicitly
deferred rather than simulated as production behavior.
