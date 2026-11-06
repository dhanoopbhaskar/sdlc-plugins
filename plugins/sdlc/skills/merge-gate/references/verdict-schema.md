# Verdict artifact schema

`verdict.md` ends with one fenced `json` block. The block is the machine-readable
verdict; the prose above it is for humans. `evals/verdict.py` validates the block
and recomputes `verdict`. A mismatch fails.

## Block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "8f3c2a1b9d4e6f708192a3b4c5d6e7f80912a3b4",
  "diff_hash": "sha256:…",
  "profile_hash": "sha256:…",
  "tier": "T2",
  "isolation": "isolated",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P0-001",
      "lens": "L1",
      "severity": "P0",
      "file": "src/auth/session.ts",
      "line": 88,
      "trigger": "request with an expired cookie plus a refreshed token",
      "consequence": "session accepted after expiry (authz bypass)",
      "fix": "compare exp before issuing the token; add a regression test",
      "absence": false,
      "accepted_risk": false
    }
  ],
  "unproven": [
    { "item": "load test at production cardinality", "accepted": false, "reason": "no capacity environment" }
  ],
  "coverage_gaps": [
    { "lens": "L3", "item": "load test at production cardinality", "t2_relevant": true }
  ],
  "blocked_env": [],
  "signoff": { "approver": "name", "date": "2026-11-06", "scope": "T2 auth change" },
  "verdict": "BLOCK"
}
```

## Fields

| Field | Type | Rule |
|---|---|---|
| `schema` | string | must be `sdlc.verdict/v1` |
| `base_sha` | string | non-empty; the merge-base commit |
| `diff_hash` | string | non-empty; hash of the reviewed diff |
| `profile_hash` | string | non-empty; hash of the base-commit profile |
| `tier` | `T0`/`T1`/`T2`/`T3` | re-derived by the gate, not copied from `plan` blindly |
| `isolation` | `isolated`/`single-context` | T2 and T3 require `isolated` |
| `acs` | `confirmed`/`unconfirmed` | `unconfirmed` forces `UNSCOPED` |
| `findings` | array | see below |
| `unproven` | array | `{item, accepted, reason}`; `accepted: false` blocks |
| `coverage_gaps` | array | `{lens, item, t2_relevant}`; a `t2_relevant` gap must also appear in `unproven` |
| `blocked_env` | array of strings | non-empty forces `BLOCKED-ENV`; includes an unavailable restricted sandbox or tree-scoped approval |
| `signoff` | object or null | `{approver, date, scope}`; required for T2/T3 `MERGE-READY` |
| `verdict` | string | must equal the computed verdict exactly |

## Findings

Required: `id`, `lens`, `severity`, `file`, `line`, `trigger`, `consequence`, `fix`.

- `id` is unique within the artifact.
- `lens` is `L1`, `L2`, or `L3`.
- `severity` is `P0`, `P1`, `P2`, or `P3`. `P2` and `P3` never block.
- `line` is a positive integer. For an absence finding, point at the deletion or the call site.
- `absence: true` requires `absence_of` with a non-empty description.
- `accepted_risk: true` requires `risk_acceptance` with `approver`, `date`, and `rationale`.
- No secret values. Cite a masked prefix; the parser rejects high-confidence secret patterns.

## Verdict precedence

First matching row wins:

```
P0 not risk-accepted                    → BLOCK
else P1 not risk-accepted               → FIX
else a required command cannot run      → BLOCKED-ENV
else ACs missing or unconfirmed         → UNSCOPED
else T2/T3 without isolated passes      → BLOCKED-UNVERIFIED
else any UNPROVEN not accepted          → BLOCKED-UNVERIFIED
else T2/T3 without sign-off             → AWAITING-SIGNOFF
else T0/T1 without isolated passes      → MERGE-READY (SINGLE-CONTEXT)
else                                    → MERGE-READY
```

Qualifiers are appended in this order: `SINGLE-CONTEXT`, `SIGNED`,
`RISK-ACCEPTED`. For example `MERGE-READY (SIGNED, RISK-ACCEPTED)`.

## Rules the parser enforces

- `verdict` equals the computed string.
- `T2`/`T3` findings are never merged without `isolation: "isolated"` and a `signoff`.
- A `t2_relevant` coverage gap is represented in `unproven`.
- Every finding has a trigger; every absence finding has `absence_of`.
- No quoted secrets.
