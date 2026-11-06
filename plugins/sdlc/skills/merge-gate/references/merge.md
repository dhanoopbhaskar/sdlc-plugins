# Phase 4 — Merge

Turn three independent passes into one auditable verdict. No new findings are invented here.

## 1. Dedupe by owner

Every checklist item has exactly one owning lens. If two lenses report the same defect:

- keep the finding under the owning lens;
- add `also: L2` or `also: L3` to it;
- delete the duplicate. Never double-count severity.

Ownership reminders: authz/authn → L2; non-security guards → L1; migrations, rollback, capacity → L3.

## 2. Severity

| Severity | Definition |
|---|---|
| P0 | data loss, authz bypass, secret exposure, irreversible destructive action |
| P1 | correctness bug or side effect likely to reach production |
| P2 | real risk or quality issue with no immediate failure path — never blocks |
| P3 | nit, style, naming, non-blocking observation — never blocks |

Rules:

- Severity describes consequence, not effort or taste.
- A missing test for a P0/P1 path is P1, not P3.
- A finding with no concrete trigger is deleted, not downgraded.
- Do not inflate P2 to P1 to force a fix. Do not deflate P1 to P2 to unblock.

## 3. Promote coverage gaps

A lens's `could not check` that touches a T2 concern becomes an `unproven` item with `accepted: false`. It cannot be absorbed by a green verdict.

Also add it to `coverage_gaps` with `t2_relevant: true`. The parser rejects a T2-relevant gap that is missing from `unproven`.

## 4. Risk acceptance

Only a named human can accept risk. Each acceptance records:

```json
{
  "id": "P0-001",
  "approver": "<name>",
  "date": "YYYY-MM-DD",
  "rationale": "<why the risk is acceptable and what compensates>"
}
```

The finding is still printed in full. The verdict keeps the qualifier `RISK-ACCEPTED`. A finding cannot be accepted by the reviewer agent on its own authority.

## 5. T2 sign-off

T2 `MERGE-READY` requires:

```json
{ "approver": "<name>", "date": "YYYY-MM-DD", "scope": "<what was signed>" }
```

Until then the state is `AWAITING-SIGNOFF`. "Signed" is not a synonym for "reviewed".

## 6. Compute the verdict

Apply the arithmetic in order; the first match wins:

```
P0 not risk-accepted                    → BLOCK
else P1 not risk-accepted               → FIX
else a required command cannot run      → BLOCKED-ENV
else ACs missing or unconfirmed         → UNSCOPED
else T2 without isolated passes         → BLOCKED-UNVERIFIED
else any UNPROVEN not accepted          → BLOCKED-UNVERIFIED
else T2 without sign-off                → AWAITING-SIGNOFF
else T0/T1 without isolated passes      → MERGE-READY (SINGLE-CONTEXT)
else                                    → MERGE-READY
```

Append qualifiers in this order: `SINGLE-CONTEXT`, `SIGNED`, `RISK-ACCEPTED`. Example: `MERGE-READY (SIGNED, RISK-ACCEPTED)`.

Then run `python3 evals/verdict.py <artifact>` against the block. If it disagrees, the artifact is wrong, not the parser.

## 7. `verdict.md` template

```markdown
# Verdict — <slug>

<three sentences: what changed, what proved it, what the verdict is.>

## Findings

### P1-001 · L1 · src/orders.ts:42

Trigger:     a client retries after the response times out
Consequence: a second order row is created
Fix:         key the write by request id

## Unproven

- prod-cardinality load test — no capacity environment.

## Coverage

- L1: checked state, ordering, retries, tests.
- L2: checked authz, injection, secrets.
- L3: not applicable — no deployable change.

## Verdict block

```json
{ "...": "sdlc.verdict/v1" }
```
```

## 8. Final self-check

- [ ] Every finding has a trigger and a `file:line`.
- [ ] Every absence finding points at a deletion or call site.
- [ ] No secret values; masked prefixes only.
- [ ] P2/P3 are listed and did not block.
- [ ] Every T2-relevant coverage gap is in `unproven`.
- [ ] `isolation` matches what actually happened.
- [ ] `tier` came from the base profile plus the diff.
- [ ] `diff_hash` matches the bytes reviewed.
- [ ] `python3 evals/verdict.py verdict.md` prints `OK`.
