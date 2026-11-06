# Cache key omits the tenant (TypeScript)

**Fixture:** `m2/05-ts-cache-key-tenant`  
**Stack:** typescript  
**Tier:** T2  
**Expected verdict:** `FIX`

## Acceptance criteria

A cached profile is never served to a different tenant.

## What the diff does

The profile cache key drops tenantId. Two tenants with the same user id share one entry, so one tenant can read another tenant's profile.

## A correct pass must

- report a present P1 finding under L1 at `cache.ts:4`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.
