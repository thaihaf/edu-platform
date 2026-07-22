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
