# Removed authorization guard (Python)

**Fixture:** `m2/01-python-absent-authz`  
**Stack:** python  
**Tier:** T2  
**Expected verdict:** `BLOCK`

## Acceptance criteria

The admin user listing remains restricted to admins.

## What the diff does

The refactor removes the admin guard from the user-listing route. No test covers the unauthenticated path, so nothing proves the route is still restricted.

## A correct pass must

- report an absence P0 finding under L2 at `app.py:7`;
- return `BLOCK`, not a softer verdict;
- keep every finding tied to a concrete trigger.
