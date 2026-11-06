# Verdict — m2/02-ts-unawaited-write

The order insert is fired without awaiting it and the handler reports success. A slow or failed insert still returns a 200 with no id, and a rejection becomes unhandled.

## Findings

### P1-001 · L1 · orders.ts:4

Trigger:     a create request whose insert is slow, rejected, or lost after the response
Consequence: the client is told the order exists while no order row is committed; no id is ever returned
Fix:         await the insert and return its id; let a rejection produce a failure response

## Coverage

- Checked: state writes, ordering, error paths.
- Not applicable: no auth, secret, or trust-boundary change.
- Not applicable: no deploy or migration change.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-02-ts-unawaited-write",
  "diff_hash": "sha256:f185743db4cf2b36e8b45362436e154e3f64955273ffc9e937d4dfe1c5f3b690",
  "profile_hash": "sha256:none",
  "tier": "T1",
  "isolation": "single-context",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L1",
      "severity": "P1",
      "file": "orders.ts",
      "line": 4,
      "trigger": "a create request whose insert is slow, rejected, or lost after the response",
      "consequence": "the client is told the order exists while no order row is committed; no id is ever returned",
      "fix": "await the insert and return its id; let a rejection produce a failure response",
      "absence": false
    }
  ],
  "unproven": [],
  "coverage_gaps": [],
  "blocked_env": [],
  "signoff": null,
  "verdict": "FIX"
}
```
