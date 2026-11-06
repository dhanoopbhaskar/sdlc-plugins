# Verdict — m0/absence

The refactor removes `@require_admin` from the admin listing with no replacement.
The route is still reachable, so this is an authorization bypass.

## Findings

### P0-001 · L2 · deleted a/app.py:9 (diff hunk 1); call site b/app.py:6

Trigger:     any unauthenticated request to `GET /admin/users`
Consequence: the endpoint returns user data without an admin check
Fix:         restore `@require_admin` on the route; add an unauthenticated-request test

## Coverage

- L1: no state, concurrency, or cache change.
- L2: authorization is the only relevant boundary.
- L3: no deploy, config, or migration change.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-absence",
  "diff_hash": "sha256:2327813e2e8c32abea5ee92e86d0a3242edc7de2a15e786131a44907248bdcfd",
  "profile_hash": "sha256:none",
  "tier": "T2",
  "isolation": "single-context",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P0-001",
      "lens": "L2",
      "severity": "P0",
      "file": "b/app.py",
      "line": 6,
      "trigger": "any unauthenticated request to GET /admin/users",
      "consequence": "the endpoint returns user data without an admin check",
      "fix": "restore @require_admin on the route; add an unauthenticated-request test",
      "absence": true,
      "absence_of": "the @require_admin decorator was removed with no replacement",
      "accepted_risk": false
    }
  ],
  "unproven": [],
  "coverage_gaps": [],
  "blocked_env": [],
  "signoff": null,
  "verdict": "BLOCK"
}
```
