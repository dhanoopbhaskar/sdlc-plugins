---
type: Discovery Ledger
title: Fixture ledger
description: Minimal coverage ledger used to test OKF bundle conformance.
evidence: unknown
generated: { by: legacy-code-discovery/0.2.1, at: 2026-11-04T00:00:00Z }
status: draft
---

# Repositories

| Repo | Root | Remote | Commit | Branch | Dirty | Submodules | Archived / fork | Deployables | Files (first-party) | Status / notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixture | /tmp/fixture | https://example.com/fixture | 0123456789abcdef0123456789abcdef01234567 | main | no | none | no | 1 | 1 | active |
| fixture-web | /tmp/fixture-web | https://example.com/fixture-web | fedcba9876543210fedcba9876543210fedcba98 | main | no | none | no | 1 | 1 | active |

# Shards

| ID | Repo | Paths / glob | Deployable unit | Files | Depth | Shard state | Owner | Started | Lease expires | Evidence | Updated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SH-001 | fixture | src/** | fixture | 1 | inventory | done | fixture-agent | 2026-11-04T00:00:00Z | 2026-11-05T00:00:00Z | confirmed | 2026-11-04T00:00:00Z | complete |

# Coverage

- Path coverage: 1 / 1 first-party paths assigned to a done shard

# Exclusions

- Fixtures / test data: tests/** — excluded from the denominator

# Budget

Not tracked in this fixture.

# Inventory-only

| Path / glob | Generator | Inputs | Runs during build? | Owner / notes |
| --- | --- | --- | --- | --- |
