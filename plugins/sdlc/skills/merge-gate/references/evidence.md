# Evidence format

A finding is a claim a human can re-check. If it cannot be triggered, it is not a finding.

## Present finding

```
### P1-001 · L1 · src/orders.ts:42

Trigger:     a client retries after the response times out
Consequence: a second order row is created
Fix:         key the write by request id; add a duplicate-delivery test
```

- `P<severity>-<seq>`: unique within the artifact. `P1-001`, `P1-002`, `P0-003`.
- `L1`/`L2`/`L3`: the owning lens. Cross-lens interest is `also: L2` on this finding, not a second finding.
- `path:line`: the line the consequence reaches. Ranges are allowed (`src/db.ts:40-58`).
- `Trigger`: a concrete input, state, or sequence. "If an attacker…" needs a reachable path, not a hypothetical.
- `Consequence`: what actually goes wrong.
- `Fix`: the smallest correct change. Not a refactor wish list.

## Absence finding

The defect is something that is not in the new file. A line number is still required; it points at the deletion or the call site.

```
### P0-002 · L2 · deleted src/auth/guard.ts:41 (diff hunk 3); call site src/routes/admin.ts:17

Trigger:     any unauthenticated request to GET /admin
Absence:     require_admin was removed with no replacement on the route
Fix:         restore the check; add an unauthenticated-request test
```

In the JSON block, set `"absence": true` and `"absence_of": "<what is missing>"`. `consequence` is still required: state what the absence allows.

## Invalid findings

Delete a finding when:

- the trigger is absent, vague, or unreachable;
- there is no `path:line`;
- it is a preference with no failure path (that is at most P3, and still needs a line);
- it duplicates another lens's finding;
- it quotes a secret value.

Do not pad the list to look thorough. A clean review with a short list is a valid result.

## Redaction

- Never quote a token, key, password, cookie, or private key.
- Cite `path:line` and a masked prefix: `sk_live_…`, `ghp_…`, `AKIA…`.
- Hash or mask values in command output. Keep the original out of the artifact.
- The parser rejects high-confidence secret patterns anywhere in the block.

## Coverage block

Every `lN.md` ends with:

```
## Coverage

- Checked: <areas actually examined>
- Not applicable: <areas with no surface in this diff>
- Could not check: <area> — <exact reason>
```

Rules:

- "Checked: everything" is not coverage. Name the areas.
- A T2-relevant `could not check` becomes an `unproven` item in the verdict.
- A `could not check` with no T2 relevance is still printed; it is not a pass.
