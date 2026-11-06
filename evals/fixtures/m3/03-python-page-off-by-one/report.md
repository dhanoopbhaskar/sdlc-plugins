# Investigation — m3/03-python-page-off-by-one

## Symptom

A full page returns one fewer item than the requested page size.

## Reproduction

```shell
cd before
python3 -m unittest discover -s . -p 'test_*.py' -v
# test_full_page_returns_size_items
# AssertionError: Lists differ: [0, 1, 2] != [0, 1, 2, 3]
```

## Cause

The slice end is computed as `start + size - 1`, which is an off-by-one error: a Python
slice end is exclusive, so the last item of every full page is dropped.

## Evidence

- `app.py:3` — `end = start + size - 1` subtracts one from the exclusive end.
- `app.py:4` — `items[start:end]` therefore stops one short.
- `test_app.py:7` — a ten-item list with page 1 and size 4 returns `[0, 1, 2]`.

## Alternatives ruled out

- The caller passes a short list — the input has ten items and asks for four.
- Page numbering is zero-based — page 1 of size 4 returns three items under every
  interpretation of a full page.

## Fix

- `app.py` — compute `end = start + size`; slicing already clamps the last partial page.

## Proof

```
proof:          REGRESSION-TEST
test:           test_app.PaginationTest.test_full_page_returns_size_items
before:         exit 1 — AssertionError: Lists differ: [0, 1, 2] != [0, 1, 2, 3]
after:          exit 0 — 2 passed
suite:          exit 0 — 2 passed
```

## Report block

```json
{
  "schema": "sdlc.investigation/v1",
  "diff_hash": "sha256:386b279a4da5be40ea98ec2da9006666761dcc2cb37880b6fc2218c8106e5573",
  "symptom": "A full page returns one fewer item than the requested page size.",
  "trigger": "request page 1 with size 4 from a ten-item list",
  "cause": "The slice end is computed as start + size - 1, which is an off-by-one error: a Python slice end is exclusive, so the last item of every full page is dropped.",
  "evidence": [
    "app.py:3 — end = start + size - 1 subtracts one from the exclusive end",
    "app.py:4 — items[start:end] therefore stops one short",
    "test_app.py:7 — a ten-item list with page 1 and size 4 returns [0, 1, 2]"
  ],
  "alternatives": [
    "the caller passes a short list — the input has ten items and asks for four",
    "page numbering is zero-based — page 1 of size 4 returns three items under every interpretation of a full page"
  ],
  "fix": [
    "app.py: compute end = start + size; slicing already clamps the last partial page"
  ],
  "proof": {
    "kind": "REGRESSION-TEST",
    "test": "test_app.PaginationTest.test_full_page_returns_size_items",
    "before": "exit 1 — AssertionError: Lists differ: [0, 1, 2] != [0, 1, 2, 3]",
    "after": "exit 0 — 2 passed",
    "suite": "exit 0 — 2 passed"
  },
  "confidence": "confirmed",
  "unproven": []
}
```
