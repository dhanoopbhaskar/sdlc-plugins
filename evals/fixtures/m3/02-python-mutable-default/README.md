# Mutable default argument leaks state between calls (Python)

**Fixture:** `m3/02-python-mutable-default`  
**Stack:** python  
**Expected proof:** `REGRESSION-TEST`

## Symptom

Independent calls to `add_tag("b")` return the tags from earlier calls. The second call
returns `["a", "b"]` instead of `["b"]`.

## Reproduction

```shell
cd before
python3 -m unittest discover -s . -p 'test_*.py' -v
```

The test fails with `Lists differ: ['a', 'b'] != ['b']`.

## A correct pass must

- name the mechanism: the mutable default list is created once and shared by every call;
- cite the function signature as `file:line`;
- rule out caller-owned state and module globals;
- keep the explicit-list behaviour and record a regression test that fails on the parent
  and passes with the fix.
