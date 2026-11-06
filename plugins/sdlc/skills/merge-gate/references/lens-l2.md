# Lens L2 — Security and trust boundaries

You are the L2 pass. Input: the diff, the ACs, `proof.md` (facts, no findings), and this file. Do not read `l1.md`, `l3.md`, or `verdict.md`.

## You own

- Authentication and authorization policy
- Trust-boundary input validation
- Injection
- Secrets and credential handling
- Cryptographic choices
- Network and path attacks
- LLM trust boundaries
- Dependencies
- Data exposure
- Transport, sessions, and headers
- Uploads and archive extraction

## Checklist

### AuthN and AuthZ

- Is the check present, and does it run *before* the effect?
- Is the principal the one the resource belongs to (no IDOR)?
- Is tenant scoping enforced on every read and write?
- Can a lower privilege reach a higher-privilege path?

L2 owns an authz/authn check whether it was removed, is present, or is wrong. L1 owns non-security guards (bounds, null, flags).

### Input and injection

- Is validation at the trust boundary, not deep in the call stack?
- Allowlist or denylist? Prefer allowlist.
- SQL/ORM raw fragments, shell, template, log, and header injection.
- SSRF, path traversal, open redirect, unsafe deserialization.

### Secrets

- Hardcoded, logged, in errors, in URLs, in fixtures, in telemetry.
- Is a secret compared in constant time where it matters?
- Are keys rotated and scoped, or shared forever?

### Crypto and randomness

- Algorithms and modes.
- Randomness source.
- Constant-time comparison for tokens and MACs.

### LLM boundary

- Is retrieved or tool content treated as instructions?
- Can model output reach code, SQL, shell, or a privileged tool unvalidated?
- Can a tool call exfiltrate secrets or data?
- Is the system prompt protected from content it reads?

### Dependencies

- New package, typosquat, unpinned version, install-time script.
- Does it need the network or credentials at install time?

### Data exposure

- PII in logs, errors, responses, traces.
- Returning more fields than the caller needs.
- Cache headers on authenticated responses.

### Transport and sessions

- CORS, CSRF, session and cookie flags.
- TLS assumptions.
- Upload limits, content-type checks, archive extraction bounds.

## Handoffs

- A non-security guard was deleted or relaxed → L1.
- A migration or config default is unsafe → L3.
- Logging or alerting is missing → L3.
- Data retention → L3.

Do not file a finding owned by another lens. Add `also: L1` or `also: L3` instead.

## Evidence

Present finding:

```
### P0-001 · L2 · path/to/file.ts:88
Trigger:     the concrete request, payload, or sequence
Consequence: the boundary that fails and what it exposes
Fix:         the smallest correct change
```

Absence finding:

```
### P0-002 · L2 · deleted path/to/guard.ts:41 (diff hunk 3); call site path/to/route.ts:17
Trigger:     any unauthenticated request to the route
Absence:     the authorization check was removed with no replacement
Fix:         restore the check; add a negative test
```

A finding without a concrete trigger is invalid. Delete it.

## Coverage

End `l2.md` with:

```
## Coverage
- Checked: ...
- Not applicable: ...
- Could not check: ...
```

A T2-relevant `could not check` must be repeated in the verdict's `unproven` list.
