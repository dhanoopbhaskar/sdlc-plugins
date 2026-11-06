# Swallowed write error with a success fallback (Go)

**Fixture:** `m2/07-go-swallowed-error`  
**Stack:** go  
**Tier:** T1  
**Expected verdict:** `FIX`

## Acceptance criteria

A failed write is reported to the caller as a failure.

## What the diff does

A failed save is logged and ignored, then the handler returns success. The caller cannot distinguish a committed record from a dropped one.

## A correct pass must

- report a present P1 finding under L1 at `store.go:12`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.
