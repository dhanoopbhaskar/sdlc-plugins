# Cache key omits the tenant (Python)

**Fixture:** `m3/01-python-cache-key-tenant`  
**Stack:** python  
**Expected proof:** `REGRESSION-TEST`

## Symptom

A user who belongs to two tenants receives the first tenant's profile from the second
tenant's request. The failure is deterministic and happens in one process.

## Reproduction

```shell
cd before
python3 -m unittest discover -s . -p 'test_*.py' -v
```

The test fails with `'tenant-a' != 'tenant-b'`.

## A correct pass must

- name the mechanism: `load_profile` keys the cache by `user_id` only, so the tenant is
  absent from the key;
- cite the cache key site and the call site as `file:line`;
- rule out a cross-request cache leak and stale fixture data;
- fix the key, not the assertion, and record a regression test that fails on the parent and
  passes with the fix.
