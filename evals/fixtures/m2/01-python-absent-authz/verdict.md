# Verdict — m2/01-python-absent-authz

The refactor removes the admin guard from the user-listing route. No test covers the unauthenticated path, so nothing proves the route is still restricted.

## Findings

### P0-001 · L2 · app.py:7

Trigger:     any unauthenticated request to GET /admin/users
Absence:     the @require_admin decorator was removed with no replacement
Fix:         restore the guard on the route; add an unauthenticated-request test

## Coverage

- Checked: routing, authorization, tests.
- Checked: authorization is the only boundary on this route.
- Not applicable: no deploy, config, or migration change.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-01-python-absent-authz",
  "diff_hash": "sha256:66536ff435c0ebe271c1b5011abd987e79ae83c5020ad37677a70e72d5cd5530",
  "profile_hash": "sha256:none",
  "tier": "T2",
  "isolation": "isolated",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P0-001",
      "lens": "L2",
      "severity": "P0",
      "file": "app.py",
      "line": 7,
      "trigger": "any unauthenticated request to GET /admin/users",
      "consequence": "the endpoint returns every user's email without an admin check",
      "fix": "restore the guard on the route; add an unauthenticated-request test",
      "absence": true,
      "absence_of": "the @require_admin decorator was removed with no replacement"
    }
  ],
  "unproven": [],
  "coverage_gaps": [],
  "blocked_env": [],
  "signoff": null,
  "verdict": "BLOCK"
}
```
