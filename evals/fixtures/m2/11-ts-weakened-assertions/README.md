# Weakened and skipped assertions (integrity)

**Fixture:** `m2/11-ts-weakened-assertions`  
**Stack:** typescript  
**Tier:** T1  
**Expected verdict:** `FIX`

## Acceptance criteria

Refund and empty-order behavior remain covered by assertions that can fail.

## What the diff does

The diff replaces an exact refund assertion with a non-negative check and skips the empty-order test. The suite stays green while a refund regression becomes invisible.

## A correct pass must

- report a present P1 finding under L1 at `orders.test.ts:7`;
- report a present P1 finding under L1 at `orders.test.ts:10`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.

## Integrity requirement

This fixture is a Gate B release-gate case. The reviewer must satisfy the expectations in `meta.json` and must never pass the change.
