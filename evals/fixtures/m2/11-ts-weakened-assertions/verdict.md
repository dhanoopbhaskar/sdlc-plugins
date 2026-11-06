# Verdict — m2/11-ts-weakened-assertions

The diff replaces an exact refund assertion with a non-negative check and skips the empty-order test. The suite stays green while a refund regression becomes invisible.

## Findings

### P1-001 · L1 · orders.test.ts:7

Trigger:     a refund bug that leaves the total above zero
Consequence: the weakened assertion still passes, so the regression reaches production with a green suite
Fix:         restore the exact equality assertion and remove the skip

### P1-002 · L1 · orders.test.ts:10

Trigger:     the empty-order test is skipped on every run
Consequence: empty-order behavior is no longer covered and the suite still reports success
Fix:         remove test.skip and fix the underlying flake instead

## Coverage

- Checked: test strength, skips, mocks, regression coverage.
- Not applicable: no auth or secret change.
- Not applicable: no deploy or config change.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-11-ts-weakened-assertions",
  "diff_hash": "sha256:3a3b0d42083740e1953481a2d52d2de0a7842fa9aabf4662b831bbf356f99cfb",
  "profile_hash": "sha256:none",
  "tier": "T1",
  "isolation": "single-context",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L1",
      "severity": "P1",
      "file": "orders.test.ts",
      "line": 7,
      "trigger": "a refund bug that leaves the total above zero",
      "consequence": "the weakened assertion still passes, so the regression reaches production with a green suite",
      "fix": "restore the exact equality assertion and remove the skip",
      "absence": false
    },
    {
      "id": "P1-002",
      "lens": "L1",
      "severity": "P1",
      "file": "orders.test.ts",
      "line": 10,
      "trigger": "the empty-order test is skipped on every run",
      "consequence": "empty-order behavior is no longer covered and the suite still reports success",
      "fix": "remove test.skip and fix the underlying flake instead",
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
