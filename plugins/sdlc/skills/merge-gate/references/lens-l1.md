# Lens L1 — Side effects and state

You are the L1 pass. Input: the diff, the ACs, `proof.md` (facts, no findings), and this file. Do not read `l2.md`, `l3.md`, or `verdict.md`.

## You own

- Mutable state and partial writes
- Ordering and atomicity
- Idempotency and retries
- Error paths and swallowed failures
- Dropped or relaxed non-security guards (bounds, null, flags)
- Input edges
- Concurrency and TOCTOU
- Resources and leaks
- Cache key composition and invalidation
- Weakened or deleted tests
- Unsafe defaults
- Time and expiry

## Checklist

### State and atomicity

- Does every write either complete or roll back?
- Are multi-step operations transactional where they must be?
- Can a retry duplicate a side effect?

### Ordering and idempotency

- Is the side effect committed before the response claims success?
- Are at-least-once consumers safe?
- Can a double-submit create a second record?

### Error paths

- Is an exception swallowed or converted to a success?
- Does a fallback hide a failure the caller must know about?
- Is cleanup skipped on throw?

### Guards and defaults

- Was validation, a bounds check, a null check, or a feature flag removed or relaxed? (Authz/authn belongs to L2.)
- Does a missing value fall back to something unsafe?
- Are config typos tolerated silently?

### Inputs, concurrency, resources

- Empty, null, zero, negative, unicode, very large.
- Races, shared caches, TOCTOU, lock scope.
- Unclosed handles, unbounded growth, leaked subscriptions.

### Cache, time, tests

- Does the key include every dimension that changes the value (tenant, user, locale, version)?
- Is invalidation defined?
- Were assertions deleted, weakened, skipped, or mocked away?
- Timezone, clock skew, expiry boundaries.

## Handoffs

- The guard is authz/authn, whether removed, present, or wrong → L2.
- A migration is unsafe → L3.
- A secret is exposed → L2.
- Rollback, observability, capacity → L3.

Do not file a finding owned by another lens. Add `also: L2` or `also: L3` to your finding instead.

## Evidence

Present finding:

```
### P1-001 · L1 · path/to/file.ts:88
Trigger:     the concrete input, state, or sequence
Consequence: what actually goes wrong
Fix:         the smallest correct change
```

Absence finding:

```
### P1-002 · L1 · deleted path/to/guard.ts:41 (diff hunk 3); call site path/to/route.ts:17
Trigger:     any unauthenticated request to the route
Absence:     the check was removed with no replacement
Fix:         restore the check; add a regression test
```

A finding without a concrete trigger is invalid. Delete it.

## Coverage

End `l1.md` with:

```
## Coverage
- Checked: ...
- Not applicable: ...
- Could not check: ...
```

A T2-relevant `could not check` must be repeated in the verdict's `unproven` list.
