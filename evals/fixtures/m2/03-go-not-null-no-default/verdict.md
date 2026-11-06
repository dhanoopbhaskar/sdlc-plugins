# Verdict — m2/03-go-not-null-no-default

The migration adds a NOT NULL column to a live table with no default or backfill, and the down section is empty. Existing rows fail the constraint and a rollback has no path.

## Findings

### P1-001 · L3 · migrations/0007_add_tenant_id.sql:2

Trigger:     deploy of this migration against an invoices table that already has rows
Absence:     no DEFAULT clause and no backfill for existing rows
Fix:         add the column nullable, backfill tenant_id, then set NOT NULL in a later migration

### P1-002 · L3 · migrations/0007_add_tenant_id.sql:4

Trigger:     a rollback after this migration ships
Absence:     no down migration
Fix:         add a down step that drops the column, or document and rehearse a forward fix

## Coverage

- Not applicable: no application logic change.
- Not applicable: no auth or secret change.
- Checked: migration safety, backfill, rollback, deploy ordering.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-03-go-not-null-no-default",
  "diff_hash": "sha256:ccecac1ba553c7b2095a96d05a3be77198105ee5abb31cfd13fdf503bec1c041",
  "profile_hash": "sha256:none",
  "tier": "T2",
  "isolation": "isolated",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L3",
      "severity": "P1",
      "file": "migrations/0007_add_tenant_id.sql",
      "line": 2,
      "trigger": "deploy of this migration against an invoices table that already has rows",
      "consequence": "every existing row violates NOT NULL, so the migration aborts and the deploy fails",
      "fix": "add the column nullable, backfill tenant_id, then set NOT NULL in a later migration",
      "absence": true,
      "absence_of": "no DEFAULT clause and no backfill for existing rows"
    },
    {
      "id": "P1-002",
      "lens": "L3",
      "severity": "P1",
      "file": "migrations/0007_add_tenant_id.sql",
      "line": 4,
      "trigger": "a rollback after this migration ships",
      "consequence": "the down section is empty, so the column and its constraint stay in place",
      "fix": "add a down step that drops the column, or document and rehearse a forward fix",
      "absence": true,
      "absence_of": "no down migration"
    }
  ],
  "unproven": [],
  "coverage_gaps": [],
  "blocked_env": [],
  "signoff": null,
  "verdict": "FIX"
}
```
