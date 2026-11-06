# NOT NULL column with no default and no down path (Go/SQL)

**Fixture:** `m2/03-go-not-null-no-default`  
**Stack:** go  
**Tier:** T2  
**Expected verdict:** `FIX`

## Acceptance criteria

Existing invoices can be migrated safely, and the migration can be rolled back.

## What the diff does

The migration adds a NOT NULL column to a live table with no default or backfill, and the down section is empty. Existing rows fail the constraint and a rollback has no path.

## A correct pass must

- report an absence P1 finding under L3 at `migrations/0007_add_tenant_id.sql:2`;
- report an absence P1 finding under L3 at `migrations/0007_add_tenant_id.sql:4`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.
