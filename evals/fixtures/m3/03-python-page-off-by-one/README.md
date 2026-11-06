# Pagination slice drops the last item of a page (Python)

**Fixture:** `m3/03-python-page-off-by-one`  
**Stack:** python  
**Expected proof:** `REGRESSION-TEST`

## Symptom

A full page returns one fewer item than the requested page size. Page 1 with size 4
returns three items.

## Reproduction

```shell
cd before
python3 -m unittest discover -s . -p 'test_*.py' -v
```

The test fails with `Lists differ: [0, 1, 2] != [0, 1, 2, 3]`.

## A correct pass must

- name the mechanism: the slice end is `start + size - 1` while Python slice ends are
  exclusive, an off-by-one that drops the last item;
- cite the end computation and the slice as `file:line`;
- rule out short input and zero-based page numbering;
- keep the last-page behaviour and record a regression test that fails on the parent and
  passes with the fix.
