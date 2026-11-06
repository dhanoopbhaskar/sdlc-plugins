# Verdict — m2/07-go-swallowed-error

A failed save is logged and ignored, then the handler returns success. The caller cannot distinguish a committed record from a dropped one.

## Findings

### P1-001 · L1 · store.go:12

Trigger:     the database rejects or loses the write while the handler continues
Consequence: the caller receives OK for a record that was never persisted
Fix:         return the error after logging it; test the failed-write path

## Coverage

- Checked: error paths, partial writes, success signaling.
- Not applicable: no auth, secret, or injection surface.
- Not applicable: no deploy or config change.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-07-go-swallowed-error",
  "diff_hash": "sha256:18ffd0c58a540682f1f94909fbad63e11e69e0e752a77a9014a9b0057f6c42de",
  "profile_hash": "sha256:none",
  "tier": "T1",
  "isolation": "single-context",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L1",
      "severity": "P1",
      "file": "store.go",
      "line": 12,
      "trigger": "the database rejects or loses the write while the handler continues",
      "consequence": "the caller receives OK for a record that was never persisted",
      "fix": "return the error after logging it; test the failed-write path",
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
