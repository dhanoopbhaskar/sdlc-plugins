# Verdict — m2/05-ts-cache-key-tenant

The profile cache key drops tenantId. Two tenants with the same user id share one entry, so one tenant can read another tenant's profile.

## Findings

### P1-001 · L1 · cache.ts:4

Trigger:     tenant B loads the profile of a user id already cached by tenant A
Consequence: tenant B receives tenant A's cached profile; the key no longer separates tenants
Fix:         include tenantId in the key; add a two-tenant isolation test

## Coverage

- Checked: cache key composition, invalidation, tenant scoping.
- Checked: the key change also crosses a tenant boundary; recorded as also: L2.
- Not applicable: no deploy or migration change.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-05-ts-cache-key-tenant",
  "diff_hash": "sha256:9ba394cae3dff94c17bf197fd6d6ad6e2116ff0a244dad763a6b45828d3e1228",
  "profile_hash": "sha256:none",
  "tier": "T2",
  "isolation": "isolated",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L1",
      "severity": "P1",
      "file": "cache.ts",
      "line": 4,
      "trigger": "tenant B loads the profile of a user id already cached by tenant A",
      "consequence": "tenant B receives tenant A's cached profile; the key no longer separates tenants",
      "fix": "include tenantId in the key; add a two-tenant isolation test",
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
