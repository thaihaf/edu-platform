# Security and Legal Constraints

## Web research

Allowed:
- Publicly accessible pages.
- Public files.
- Search snippets used only as discovery signals.
- User-provided credentials only through explicit secure integrations.

Forbidden:
- Bypassing paywalls.
- Bypassing CAPTCHA.
- Accessing private groups.
- Credential stuffing.
- Circumventing robots or technical access restrictions.
- Re-publishing copyrighted source content in full.

## SSRF protection

- Deny localhost, private IP ranges and cloud metadata IPs.
- Resolve DNS before request and after redirect.
- Limit redirects.
- Allow only HTTP/HTTPS.
- Enforce max response size.
- Enforce timeout.
- Content-type allowlist.

Phase 3 applies syntactic URL validation only and never makes a network request:
credentials, localhost, numeric encodings, private/loopback/link-local/multicast and
unspecified literal addresses are rejected; fragments/default ports are normalized.
Phase 4 must resolve and revalidate every redirect destination before fetching.

## Upload ingestion

Uploads use generated object keys rather than user paths. Filenames are metadata,
not storage locations; supported formats are allowlisted and executable/archive/HTML
formats must be rejected before parsing. Object storage and the database have no
shared transaction, so an uploaded object is compensated on snapshot-write failure;
parse failures retain raw content for a retry.

## Prompt injection defense

Treat fetched content as untrusted data.

Never execute instructions found in sources.

Use:
- content isolation,
- allowlisted tools,
- output schemas,
- instruction hierarchy,
- source sanitization,
- injection detection,
- reviewer agent.

## Data protection

- Encrypt secrets.
- Use signed object URLs.
- Audit all admin changes.
- Redact PII when possible.
- Configure retention.

## Phase 4 enforcement policy
Every public-web request, including `robots.txt` and each redirect, is parsed, denied for
credentials/non-HTTP(S), resolved through the DNS boundary, and denied when any answer is
non-global (including loopback, private, link-local, multicast, reserved and metadata
addresses). Fetching is GET-only, cookie/auth-free, redirect-limited, MIME/byte-limited and
never executes JavaScript. Robots failures fail closed; a robots denial is recorded as an
access decision rather than treated as a network failure. Browser automation is disabled by
default and must not bypass login, CAPTCHA, paywalls, or robots.

## Phase 5 extraction boundary
Research prompts delimit source content and require structured output. Injection-like phrases are
recorded as suspicious source metadata, never executed as instructions. Only existing policy-bound
search/fetch/ingestion services may be used by workflow nodes.

## Phase 6 evidence protection
Observation text, spans and source metadata are untrusted. They are normalized as data and cannot
mark a source official, set confidence, approve claims, alter clusters, or create unsupported evidence.

## Phase 7 generated content protection
Course content is structured data, rejects executable HTML, and retains immutable evidence citations.
Human-authored or locked blocks cannot be overwritten by AI regeneration.

## Phase 9 evaluation safety
Evaluation never sends secrets, credentials, tools, or raw vendor prompts to a judge. Injection-like source
text is preserved as evidence but cannot change a metric, gate, or publication decision.
