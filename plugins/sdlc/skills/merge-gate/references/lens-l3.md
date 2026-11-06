# Lens L3 — Operational blast radius

You are the L3 pass. Input: the diff, the ACs, `proof.md` (facts, no findings), and this file. Do not read `l1.md`, `l2.md`, or `verdict.md`.

## You own

- Migrations and backfills
- Backwards compatibility
- Config and environment changes
- Feature flags
- Deploy ordering
- Observability
- Failure modes and resilience
- Cost
- Data retention and deletion
- Rollback
- Capacity

## Checklist

### Migrations

- Is there a forward and a down path?
- Lock time on the largest table.
- Backfill strategy, batching, and resumability.
- Nullable/default added before code depends on it.
- Can the old and new code run at the same time?

### Compatibility

- API, schema, and event contracts.
- Consumers you do not control.
- Version negotiation and deprecation window.

### Config and environment

- New required variable? Who provisions it, and in which environments?
- Unsafe default if it is missing.
- Drift between environments.
- Secret provisioning, not just secret reference.

L2 owns the secret value; you own its provisioning and rotation path.

### Flags and deploy order

- Default state on deploy.
- Kill switch and owner.
- Cleanup plan.
- Code before schema, or schema before code? Is the rolling deploy safe at every step?

### Observability

- Logs, metrics, traces for the new path.
- Alerting and ownership.
- Errors a human can act on.

### Failure modes

- Dependency down, timeout, retry storm, circuit breaking.
- Queue backpressure and dead letters.
- Partial failure and recovery.

### Cost, retention, capacity

- Query plans, N+1, storage, egress.
- Data retention and deletion obligations.
- Indexes, cardinality, quotas.
- Can this be reverted without data loss?

## Handoffs

- Code correctness, ordering, or idempotency → L1.
- Auth policy, injection, secrets → L2.
- Test coverage of the operational path → L1.

Do not file a finding owned by another lens. Add `also: L1` or `also: L2` instead.

## Evidence

Present finding:

```
### P1-001 · L3 · path/to/migration.sql:12
Trigger:     deploy of this migration against a live table with existing rows
Consequence: the column is NOT NULL with no default; the deploy fails
Fix:         add a nullable column, backfill, then add the constraint
```

Absence finding:

```
### P1-002 · L3 · deleted path/to/down.sql:1 (diff hunk 2); call site path/to/migrate.ts:30
Trigger:     a rollback after this migration ships
Absence:     no down migration exists
Fix:         add the down migration and rehearse it
```

A finding without a concrete trigger is invalid. Delete it.

## Coverage

End `l3.md` with:

```
## Coverage
- Checked: ...
- Not applicable: ...
- Could not check: ...
```

A T2-relevant `could not check` must be repeated in the verdict's `unproven` list.
