# Investigation — m3/02-python-mutable-default

## Symptom

Independent calls to `add_tag` accumulate tags instead of starting from an empty list.

## Reproduction

```shell
cd before
python3 -m unittest discover -s . -p 'test_*.py' -v
# test_calls_do_not_share_state
# AssertionError: Lists differ: ['a', 'b'] != ['b']
```

## Cause

The mutable default list in the function signature is created once at definition time and
shared by every call that omits the argument, so tags accumulate across independent calls.

## Evidence

- `app.py:1` — `tags=[]` is a single list object created when the module loads.
- `test_app.py:7` — the second one-argument call sees the first call's tag.

## Alternatives ruled out

- The caller passes the same list — the failing call omits the argument entirely.
- Module-level global state — there is no other mutable state in the module.

## Fix

- `app.py` — default to `None` and create a fresh list inside the function; keep the
  explicit-list path unchanged.

## Proof

```
proof:          REGRESSION-TEST
test:           test_app.MutableDefaultTest.test_calls_do_not_share_state
before:         exit 1 — AssertionError: Lists differ: ['a', 'b'] != ['b']
after:          exit 0 — 2 passed
suite:          exit 0 — 2 passed
```

## Report block

```json
{
  "schema": "sdlc.investigation/v1",
  "diff_hash": "sha256:d0666f96e77d66924333dbb1e95b4db82c9d132e9adb834b4affc5a89bbaefed",
  "symptom": "Independent calls to add_tag accumulate tags instead of starting from an empty list.",
  "trigger": "call add_tag twice with one argument and no explicit list",
  "cause": "The mutable default list in the function signature is created once at definition time and shared by every call that omits the argument, so tags accumulate across independent calls.",
  "evidence": [
    "app.py:1 — tags=[] is a single list object created when the module loads",
    "test_app.py:7 — the second one-argument call sees the first call's tag"
  ],
  "alternatives": [
    "the caller passes the same list — the failing call omits the argument entirely",
    "module-level global state — there is no other mutable state in the module"
  ],
  "fix": [
    "app.py: default to None and create a fresh list inside the function; keep the explicit-list path unchanged"
  ],
  "proof": {
    "kind": "REGRESSION-TEST",
    "test": "test_app.MutableDefaultTest.test_calls_do_not_share_state",
    "before": "exit 1 — AssertionError: Lists differ: ['a', 'b'] != ['b']",
    "after": "exit 0 — 2 passed",
    "suite": "exit 0 — 2 passed"
  },
  "confidence": "confirmed",
  "unproven": []
}
```
