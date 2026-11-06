# Investigation — m3/01-python-cache-key-tenant

## Symptom

A user in two tenants receives the first tenant's profile when requesting the second
tenant's data.

## Reproduction

```shell
cd before
python3 -m unittest discover -s . -p 'test_*.py' -v
# test_same_user_in_different_tenants_does_not_share
# AssertionError: 'tenant-a' != 'tenant-b'
```

## Cause

`load_profile` keys the cache by `user_id` only, so the tenant never enters the cache
key and the first tenant's value is returned for the same user in every tenant.

## Evidence

- `app.py:7` — `get_or_compute` accepts a single `user_id` as the key.
- `app.py:14` — `load_profile` passes `user_id` and drops `tenant_id`.
- `test_app.py:7` — two tenants with the same user id receive different payloads.

## Alternatives ruled out

- A process-wide cache leak across requests — the same `Cache` instance is passed
  explicitly and the failure reproduces in one process.
- Stale fixture data — `fetch` is a pure lambda and the second tenant never calls it.

## Fix

- `app.py` — key the cache by `(tenant_id, user_id)` and pass both from `load_profile`.

## Proof

```
proof:          REGRESSION-TEST
test:           test_app.TenantCacheTest.test_same_user_in_different_tenants_does_not_share
before:         exit 1 — AssertionError: 'tenant-a' != 'tenant-b'
after:          exit 0 — 1 passed
suite:          exit 0 — 1 passed
```

## Report block

```json
{
  "schema": "sdlc.investigation/v1",
  "diff_hash": "sha256:4a5db6befa2c0f9e80be96c6b72362e5cfa84ebdf7de0fe013b0532041bc6116",
  "symptom": "A user in two tenants receives the first tenant's profile when requesting the second tenant's data.",
  "trigger": "request the same user id under two different tenants with a warm cache",
  "cause": "load_profile keys the cache by user_id only, so the tenant never enters the cache key and the first tenant's value is returned for the same user in every tenant.",
  "evidence": [
    "app.py:7 — get_or_compute accepts a single user_id as the key",
    "app.py:14 — load_profile passes user_id and drops tenant_id",
    "test_app.py:7 — two tenants with the same user id receive different payloads"
  ],
  "alternatives": [
    "process-wide cache leak across requests — the same Cache instance is passed explicitly and the failure reproduces in one process",
    "stale fixture data — fetch is a pure lambda and the second tenant never calls it"
  ],
  "fix": [
    "app.py: key the cache by (tenant_id, user_id) and pass both from load_profile"
  ],
  "proof": {
    "kind": "REGRESSION-TEST",
    "test": "test_app.TenantCacheTest.test_same_user_in_different_tenants_does_not_share",
    "before": "exit 1 — AssertionError: 'tenant-a' != 'tenant-b'",
    "after": "exit 0 — 1 passed",
    "suite": "exit 0 — 1 passed"
  },
  "confidence": "confirmed",
  "unproven": []
}
```
