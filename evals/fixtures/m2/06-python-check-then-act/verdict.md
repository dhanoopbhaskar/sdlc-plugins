# Verdict — m2/06-python-check-then-act

An atomic decrement is replaced by read-modify-write. Two concurrent withdrawals can both observe a sufficient balance and overdraw the account.

## Findings

### P1-001 · L1 · wallet.py:8

Trigger:     two withdrawals of the full balance arrive between the read and the write
Consequence: both pass the balance check and the account is overdrawn
Fix:         restore the atomic conditional decrement; add a concurrent-withdrawal test

## Coverage

- Checked: concurrency, ordering, atomicity, tests.
- Not applicable: no auth or secret change.
- Not applicable: no deploy or migration change.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-06-python-check-then-act",
  "diff_hash": "sha256:95f2f4524db3e423881a109a86d643f70122ec28f2548b6f50b83ec0793ee167",
  "profile_hash": "sha256:none",
  "tier": "T2",
  "isolation": "isolated",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L1",
      "severity": "P1",
      "file": "wallet.py",
      "line": 8,
      "trigger": "two withdrawals of the full balance arrive between the read and the write",
      "consequence": "both pass the balance check and the account is overdrawn",
      "fix": "restore the atomic conditional decrement; add a concurrent-withdrawal test",
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
