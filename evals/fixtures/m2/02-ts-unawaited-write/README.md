# Database write not awaited before the response (TypeScript)

**Fixture:** `m2/02-ts-unawaited-write`  
**Stack:** typescript  
**Tier:** T1  
**Expected verdict:** `FIX`

## Acceptance criteria

Creating an order returns the persisted order id, and a failed insert is reported as a failure.

## What the diff does

The order insert is fired without awaiting it and the handler reports success. A slow or failed insert still returns a 200 with no id, and a rejection becomes unhandled.

## A correct pass must

- report a present P1 finding under L1 at `orders.ts:4`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.
