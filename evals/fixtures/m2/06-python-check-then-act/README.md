# Check-then-act race on a shared balance (Python)

**Fixture:** `m2/06-python-check-then-act`  
**Stack:** python  
**Tier:** T2  
**Expected verdict:** `FIX`

## Acceptance criteria

Concurrent withdrawals never overdraw an account.

## What the diff does

An atomic decrement is replaced by read-modify-write. Two concurrent withdrawals can both observe a sufficient balance and overdraw the account.

## A correct pass must

- report a present P1 finding under L1 at `wallet.py:8`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.
