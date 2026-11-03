# The Discovery Bundle (OKF v0.2)

The discovery dossier is an OKF v0.2 knowledge bundle: a directory of markdown files with
YAML frontmatter. The normative format is
[`code-documenter/references/SPEC.md`](../../code-documenter/references/SPEC.md); this file
defines how discovery uses it. If the two disagree, the spec wins.

## Layout

```
docs/discovery/
  index.md                      # Progressive disclosure; okf_version: "0.2"
  log.md                        # Chronological change log
  charter.md                    # Discovery Charter
  ledger.md                     # Discovery Ledger
  system.md                     # System (one-page map)
  repos/                        # Multi-repo estates only
    index.md
    <repo-slug>.md              # Repository Registry entry
    <repo-slug>/                # Optional per-repo sub-bundle
  inventory/
    index.md
    <component-slug>.md         # Component
  flows/
    index.md
    <entrypoint-slug>.md        # Entry Point
    <flow-slug>.md              # Flow
    <boundary-slug>.md          # Integration Boundary
  data/
    index.md
    <store-slug>.md             # Data Store
  rules/
    index.md
    <rule-slug>.md              # Business Rule
  risks/
    index.md
    <risk-slug>.md              # Migration Risk
  seams/
    index.md
    <seam-slug>.md              # Migration Seam
  questions/
    index.md
    <question-slug>.md          # Open Question
    <experiment-slug>.md        # Validation Experiment
```

Create only the directories that apply. Do not create empty directories just to match this
tree. Subdirectory `index.md` files are optional: write one only when it will be linked from the
parent index, otherwise link concepts directly. The discovery workflow always writes the
bundle-root `index.md` and `log.md`.

## Common frontmatter

Every concept starts from this shape. Only `type` is mandatory in OKF; discovery expects the
rest unless the field genuinely does not apply.

```yaml
---
type: Component
title: Billing Service
description: Calculates invoices, persists them, and emits billing events.
resource: repo://acme-billing/src/Billing.Api/Program.cs#L1-L40
tags: [discovery, component, dotnet, service]
repo: acme-billing
commit: 8f3c2a1b9d4e6f708192a3b4c5d6e7f80912a3b4
shard: SH-004
evidence: confirmed
generated: { by: <writer>/<version>, at: 2026-11-03T10:00:00Z }
status: draft
stale_after: 2027-02-01T00:00:00Z
sources:
  - id: billing-program
    resource: repo://acme-billing/src/Billing.Api/Program.cs#L1-L120
    title: Service registration and entry point
    last_modified: 2026-09-14T00:00:00Z
---
```

Field rules:

| Field | Use |
| --- | --- |
| `type` | One of the concept types below. |
| `title` | Human name; use the domain name, not the folder name. |
| `description` | One sentence: what it is and why it matters for migration. |
| `resource` | Canonical artifact. Use `repo://<repo-slug>/<path>#L<a>-L<b>` for code; an absolute URL for external systems. |
| `tags` | Include `discovery`, the concept kind, the stack, and the deployable unit. |
| `repo` | Repository slug from the registry, or a stable slug (usually the directory name) in a single-repo bundle. Required when all `repo://` URIs belong to one repository; must match the `<repo-slug>`. Omit it when sources span repositories and set `repo` on each source instead. |
| `commit` | Full SHA the concept was derived from. Required alongside `repo`; must match the registry entry. Omit it when sources span repositories and set `commit` on each source instead. |
| `shard` | Ledger shard ID that produced the concept. For concepts assembled across shards (for example `system.md`), record the primary shard here and list the contributing shards in the body. |
| `evidence` | `confirmed`, `corroborated`, `inferred`, or `unknown`. |
| `generated` | `{ by: <actor>, at: <ISO 8601 with offset> }`. Required on write. Use `<skill>/<version>` with the plugin version from `plugin.json`; the phase skills show concrete examples. |
| `verified` | `[{ by: <actor>, at: <ISO 8601> }]`; add only after a real check. Use `human:<id>` for human sign-off and `process:<id>` for automation. Never pre-populate. |
| `status` | `draft` until a human reviews; then `stable`. Use `deprecated` instead of deleting. `needs-review` is a review note or tag, not a lifecycle status. |
| `stale_after` | 90 days from generation is a sensible default. |

A single verification event may be written as a mapping rather than a list, but the list form is
preferred:

```yaml
verified:
  - { by: human:ahormati, at: 2026-11-04T09:30:00Z }
```

The `repo`, `commit`, `shard`, and `evidence` fields are discovery extensions, not OKF
standard fields. Strict OKF consumers should treat them as producer-defined keys, like `repo://`,
rather than as part of the normative format.

## Evidence URIs (`repo://`)

`sources[].resource` uses the same `repo://` form. The convention is:

```
repo://<repo-slug>/<path>#L<a>-L<b>
```

- `<repo-slug>` is the `repo` field of the matching Repository Registry entry, or the `repo` on
  the source entry when the concept spans repositories. In a single-repository estate with no
  registry entry, use a stable slug (usually the directory name) and record the same value in
  every concept's `repo` field.
- `<path>` is relative to the repository root.
- Resolve the URI against the registry entry's `resource` and the `commit` on the same concept
  or source entry: on a git host, `<resource>/blob/<commit>/<path>#L<a>-L<b>`. In a single-repo
  bundle, resolve it against the repository root recorded in the ledger. For an artifact with no
  remote, record its absolute URL instead.
- `repo://` is a discovery extension, not an OKF standard scheme. When a consumer cannot
  resolve it, the path plus the `repo` and `commit` fields are still readable; never encode
  credentials, tokens, or personal data in the URI. A bundle that must be consumed by strict
  OKF tooling should put a resolvable absolute URL in `sources[].resource` and keep `repo://`
  for body evidence.

**Sources spanning repositories.** A Flow, Integration Boundary, or Migration Risk may cite
code from more than one repository. In that case omit the concept-level `repo` and `commit`
and put them on each source entry:

```yaml
sources:
  - id: billing-handler
    resource: repo://acme-billing/src/Billing.Api/Controllers/InvoicesController.cs#L40-L95
    repo: acme-billing
    commit: 8f3c2a1b9d4e6f708192a3b4c5d6e7f80912a3b4
  - id: web-bff
    resource: repo://acme-web/src/bff/invoices.ts#L12-L44
    repo: acme-web
    commit: 1a2b3c4d5e6f708192a3b4c5d6e7f80912a3b4c5
```

When every source belongs to one repository, the concept-level fields remain preferred and
the per-source fields are optional. A single concept-level `repo`/`commit` pair must never be
used to paper over a multi-repository citation.

Every material claim in the body should map to one of these sources. Use footnotes keyed by
`sources[].id` when a claim needs precise attribution:

```markdown
Invoices are rounded half-up at the line level, then summed.[^billing-rounding]

[^billing-rounding]: `src/Billing.Domain/InvoiceCalculator.cs` L88–L104
```

## Evidence grades

| Grade | Meaning | May support |
| --- | --- | --- |
| `confirmed` | Read directly, ran a read-only command, or saw an authoritative artifact. | Any conclusion. |
| `corroborated` | Two or more independent indirect signals agree. | Inventory and structure; validate behavior. |
| `inferred` | Naming, convention, folder structure, or a single weak signal. | A hypothesis that needs a validation experiment. |
| `unknown` | No reliable evidence. | An open question. |

A concept's grade is the **weakest grade of its load-bearing claims**, not the average.
Behavioral claims (business rules, data ownership, runtime semantics) must be `confirmed` or
explicitly framed as a hypothesis.

Process documents (Discovery Charter, Discovery Ledger) record user answers, scope, and
planning state. They may use `confirmed` for a direct answer or an observed process fact, but
an unanswered question is not a confirmed claim; record it in `questions/` and keep the
assumption in the charter. The `evidence` values shown in the templates below are
placeholders: compute the weakest grade instead of copying a template value.

## Concept types and body templates

Templates below show abbreviated frontmatter. Merge each with the common shape above
(`repo`, `commit`, `shard`, `evidence`, `status`, `sources`) unless a field genuinely does not
apply, and replace `<writer>` with the skill that produced the concept.

### Discovery Charter

```markdown
---
type: Discovery Charter
title: Discovery Charter — <estate>
description: Destination, scope, constraints, and success criteria for this discovery.
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Destination
<target stack/platform, or "undecided — discovery must stay target-agnostic">

# Strategy
<rehost | replatform | refactor in place | rewrite | retire | undecided, and the reason>

# In scope
- Repositories: ...
- Deployable units: ...
- Data: ...
- Environments: ...

# Out of scope
...

# Constraints
- Freeze windows:
- Compliance / residency:
- Licensing:
- Downtime tolerance:
- Budget for discovery:

# Success criteria
<what decision this discovery must enable>

# Assumptions
<anything assumed because the user did not answer; each with a validation step>

# Questions asked
<question, answer, date — or "unanswered, assumed X">
```

### Discovery Ledger

```markdown
---
type: Discovery Ledger
title: Discovery Coverage Ledger
description: Shard plan, depth, status, and coverage accounting for this discovery.
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Repositories
| Repo | Root | Remote | Commit | Branch | Dirty | Submodules | Archived / fork | Deployables | Files (first-party) | Status / notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

`Repo` is the slug used in `repo://` URIs; `Root` is the local checkout that those URIs resolve
against. Record every column for a single-repository estate too, where no Repository Registry
concept exists. `Branch` is the default branch; note the checked-out branch in `Status / notes`
when it differs. `Dirty` records whether the working tree differs from `Commit`; `Status / notes`
records `active`, `blocked`, `archived`, or a short explanation.

# Shards
| ID | Repo | Paths / glob | Deployable unit | Files | Depth | Status | Owner | Started | Lease expires | Evidence | Updated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Status: `pending` | `in-progress` | `done` | `partial` | `blocked` | `skipped` | `deprecated`.
Depth: `surface` | `inventory` | `deep`.

`Owner` and `Started` are set when a shard moves to `in-progress`; `Lease expires` is a
heartbeat, with the default lease defined in [scale.md](scale.md) §4. A shard whose lease has
expired may be reclaimed.

`Notes` is mandatory for `partial`, `blocked`, `skipped`, and `deprecated`: record what remains,
the blocker, the exclusion reason, or the replacement shard. A split parent row becomes
`deprecated` with a note pointing at its children.

# Coverage
- Repo coverage: n / N repos at `surface` depth
- Deployable coverage: n / N deployables at `inventory` depth
- Entry point coverage: n / N entry points with a resolved handler
- Flow coverage: n / N selected entry points traced end to end
- Data coverage: n / N data stores with a named owner and consumers
- Risk coverage: n / N high-risk components deep-dived
- Path coverage: n / N first-party paths assigned to a `done` shard
- Paths never opened: <list or glob>
- Sampling: <method, sample size, and covered paths; if used>

# Budget
<time/token budget agreed, spent, and remaining>

# Exclusions
- Generated: <globs> — detail each generated area in `# Inventory-only`
- Vendored / third-party: <globs>
- Archived or unused: <globs, with evidence>

# Inventory-only
| Path / glob | Generator | Inputs | Runs during build? | Owner / notes |
| --- | --- | --- | --- | --- |
```

Coverage is counted in **units that matter** (deployables, entry points, data stores,
high-risk components), never in lines of code alone.

### Repository Registry (multi-repo)

```markdown
---
type: Repository Registry
title: acme/billing
description: Billing API and workers; owns invoice and payment tables.
resource: https://github.com/acme/billing
repo: acme-billing
commit: <full SHA>
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Identity
- URL:
- Root: <local checkout path>
- Commit: <full SHA>
- Branch:
- Archived: yes/no
- Submodules: <path → repo@SHA>

# Role
<what this repo contributes to the estate>

# Deployables
| Unit | Type | Artifact | Runtime |
| --- | --- | --- | --- |

# Build and run
- Build: `<declared command>` — working directory, prerequisites, source
- Test: `<declared command>` — working directory, prerequisites, source
- Run locally: `<declared command>` — working directory, prerequisites, source
- Lint: `<declared command>` — working directory, prerequisites, source
- Release: `<declared command>` — working directory, prerequisites, source
- CI: <config path>

# Cross-repo edges
| Direction | Target | Contract | Evidence |
| --- | --- | --- | --- |

# Notes
...
```

### System

```markdown
---
type: System
title: <estate or product name>
description: One-page structural and runtime map of the estate, plus the decision summary.
evidence: <weakest grade of load-bearing claims>
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Context
<users, business purpose, external actors>

# Stack and topology
Topology: <single project | monorepo | polyrepo | hybrid>; workspace roots: <paths>

| Package / project | Language | Runtime | Frameworks | Key versions | Manifest |
| --- | --- | --- | --- | --- | --- |

# Deployable units
| Unit | Repo | Runtime role | Owns data | Talks to |
| --- | --- | --- | --- | --- |

# Build and run
| Repo / unit | Build | Test | Run locally | Lint | Release | Prerequisites / credentials | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |

# Deployment surface
| Unit | Artifact / packaging | Runtime target | Environments | Config source | Scaling / schedule | Health / readiness | IaC / orchestration | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

# Runtime shape
<sync/async, request paths, batch, scheduled work, shared state>

# Data landscape
| Store | Engine | Owner | Consumers | Migration note |
| --- | --- | --- | --- | --- |

# External boundaries
| Boundary | Direction | Protocol | Contract | Owner |
| --- | --- | --- | --- | --- |

# Readiness
| Unit | Build | Run | Test | Observe | Document | Data | Owner | Blocking gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

# Migration options
| Option | Evidence for | Evidence against | Scope / affected units |
| --- | --- | --- | --- |

# Sequencing
| Order | Slice | Seam | Proves | Does not prove | Prerequisites | Rollback |
| --- | --- | --- | --- | --- | --- | --- |

# Riskiest edges
<links to risk concepts, one line each>

# Coverage
<link to the ledger; state what is not covered>

# Decision summary
<one-page map, top findings with evidence, coverage statement, ranked risks, ranked open questions, and recommended next experiments or decisions>
```

Readiness, options, and sequencing are required once `migration-seams` has run.

Section ownership: `repo-reconnaissance` owns `# Context`, `# Stack and topology`,
`# Deployable units`, `# Build and run`, and `# Deployment surface`; `system-cartography` owns
`# Runtime shape`, `# Data landscape`, and `# External boundaries`; `migration-seams` owns
`# Readiness`, `# Migration options`, `# Sequencing`, and `# Riskiest edges`; the orchestrating
parent owns `# Coverage` and `# Decision summary` and reconciles the sections returned by shard
workers.

### Component

```markdown
---
type: Component
title: Invoice Calculator
description: Pure domain logic that computes invoice totals, tax, and rounding.
resource: repo://acme-billing/src/Billing.Domain/InvoiceCalculator.cs#L88-L104
repo: acme-billing
commit: <full SHA>
shard: SH-004
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Responsibility
<one paragraph, behavioral>

# Runtime role
<library | service | worker | job | UI | gateway | shared package | data pipeline>

# Public surface
| Symbol / route / topic | Kind | Consumers | Evidence |
| --- | --- | --- | --- |

# Dependencies
- Inbound (who uses it):
- Outbound (what it uses):
- Data: <stores, tables, caches, files>

# Behavior notes
<rules, edge cases, surprising semantics — links to rule concepts>

# Tests
| Suite | Command | What it covers | Runnable here? |
| --- | --- | --- | --- |

# Observability
<logs, metrics, traces, health checks, and what they reveal; or "absent">

# Migration relevance
- Coupling: <fan-in / fan-out / cycles>
- Data gravity:
- Replaceability:
- Unknowns:

# Evidence
- <path:line> — <claim>
```

### Entry Point

```markdown
---
type: Entry Point
title: POST /invoices
description: Creates an invoice; primary write path into billing.
resource: repo://acme-billing/src/Billing.Api/Controllers/InvoicesController.cs#L40-L95
repo: acme-billing
commit: <full SHA>
shard: SH-004
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Trigger
<HTTP method + route | CLI command | queue/topic | schedule | UI event | file drop>

# Handler
<path:line and symbol>

# Inputs
| Name | Type | Required | Validation | Notes |
| --- | --- | --- | --- | --- |

# Outputs
| Name | Type | Conditions |
| --- | --- | --- |

# Flow
1. <step, with component link>
2. ...

# Side effects
<writes, events, external calls, emails, files>

# Failure behavior
<status codes, retries, dead letters, partial writes>

# Auth and tenancy
<who can call it, how tenant is resolved>

# Evidence
```

### Flow

```markdown
---
type: Flow
title: Invoice creation
description: End-to-end path from API request to ledger posting and event emission.
evidence: <weakest grade of load-bearing claims>
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Trigger
<link to entry point>

# Steps
| # | Component | Action | Sync/Async | Failure mode |
| --- | --- | --- | --- | --- |

# Transactions and consistency
<what is atomic, what is eventually consistent, compensation>

# Data touched
| Store | Operation | Key | Notes |
| --- | --- | --- | --- |

# Observability
<logs, metrics, traces, dashboards found in the repo>

# Migration notes
<which steps could move first; where the seam is>
```

### Integration Boundary

```markdown
---
type: Integration Boundary
title: Billing → ERP (SFTP)
description: Nightly invoice export consumed by the finance ERP.
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Direction
<inbound | outbound | bidirectional>

# Counterparties
| System | Owner | Environment | Contact |
| --- | --- | --- | --- |

# Protocol and contract
<HTTP/RPC/GraphQL/queue/file/SFTP/shared DB; schema or spec path; versioning>

# Cadence and volume
<per request, batch, schedule; peak size>

# Failure and recovery
<retries, dead letters, manual replay, reconciliation>

# Data classification
<personal, financial, regulated; redact values>

# Migration notes
<contract stability, who must agree, parallel-run options>
```

### Data Store

```markdown
---
type: Data Store
title: billing.invoices
description: System of record for issued invoices; shared by API and reporting.
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Engine and location
<engine + version, host class, managed/self-hosted>

# Schema
| Table / collection | Purpose | Rows (est.) | Growth | Owner |
| --- | --- | --- | --- | --- |

# Ownership
- Writing components:
- Reading components:
- Other consumers (reports, exports, ad hoc):

# Access paths
<ORM, stored procedures, raw SQL, views, CDC>

# Constraints and invariants
<keys, triggers, checks, cascades, retention>

# Sensitive data
<classification and location; never values>

# Migration notes
<data gravity, cutover options, dual-write feasibility, archival needs>
```

### Business Rule

```markdown
---
type: Business Rule
title: Line-level half-up rounding
description: Invoice lines round half-up to 2 decimals before summing.
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Trigger
<when this rule fires>

# Rule
<precise, testable statement>

# Implementation
<path:line; note duplication across components>

# Examples
| Input | Output | Source |
| --- | --- | --- |

# Exceptions
<tenant, region, product, feature-flag branches>

# Confidence
<confirmed | corroborated | inferred — and why>

# Validation
<the test or experiment that would prove this rule>

# Migration consequence
<what breaks if the new stack's default differs>
```

### Business Rule (parity hazard)

Use the standard Business Rule template with `type: Business Rule` and add these sections when
the rule is a migration hazard. Add `parity-hazard` to `tags` so these concepts can be
filtered.

```markdown
# Legacy behavior
<observed behavior, with evidence>

# Likely default in a new stack
<the default the destination stack would probably choose; label it as an assumption>

# Difference and risk
<what could change silently, and the business consequence>

# Parity test
<the test, fixture, or shadow comparison that pins the legacy behavior>
```

### Migration Risk

```markdown
---
type: Migration Risk
title: Shared invoice table across three services
description: Three deployables write the same tables, blocking independent cutover.
evidence: confirmed
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Risk
<one sentence>

# Evidence
- <path:line or command>

# Scoring
| Dimension | Score (1–5) | Rationale |
| --- | --- | --- |
| Likelihood | | |
| Impact | | |
| Detectability (5 = hard to detect) | | |
| **Priority** | likelihood × impact × detectability | |

# Affected scope
<components, flows, data, teams>

# Failure scenario
<what happens during or after migration if this is ignored>

# Decision blocked
<the migration decision this risk prevents making>

# Mitigation options
| Option | Owner | Effort | Residual risk | Prerequisites |
| --- | --- | --- | --- | --- |

# Early warning signal
<the metric, test, or check that shows this is becoming real>

# Linked concepts
```

### Migration Seam

```markdown
---
type: Migration Seam
title: Billing API façade
description: Stable HTTP surface that can front either the legacy or the new engine.
evidence: <weakest grade of load-bearing claims>
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Seam
<the boundary and why it is a seam>

# Pattern
<strangler façade | anti-corruption layer | branch by abstraction | parallel run |
event interception | database view/sync | queue bridge | retire | other>

# Prerequisites
- <contract stability, test coverage, observability, data ownership>

# Blast radius
<what changes for consumers; what must be dual-written>

# Cutover mechanics
<routing, flags, shadow traffic, reconciliation, rollback>

# Risks
<links to risk concepts>

# First slice
<the smallest end-to-end slice that proves the seam>
```

### Open Question

```markdown
---
type: Open Question
title: Who owns the nightly ERP export?
description: Ownership is undocumented; blocks scheduling the boundary migration.
evidence: unknown
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Question
<one precise question>

# Why it matters
<which decision is blocked; impact if answered either way>

# What we know
<evidence gathered so far>

# Default assumption
<what discovery assumes until answered>

# How to answer
<person, system, document, or experiment>

# Owner and due date
```

### Validation Experiment

```markdown
---
type: Validation Experiment
title: Characterize rounding across 10k historical invoices
description: Confirms the rounding rule before reimplementation.
evidence: inferred
generated: { by: <writer>/<version>, at: ... }
status: draft
---

# Hypothesis
<falsifiable statement>

# Method
<read-only query, test harness, shadow run, interview>

# Data and access needed
<redacted; note approvals>

# Success / failure criteria
<what result confirms or kills the hypothesis>

# Cost and risk
<time, environment, production impact>

# Result
<pending | confirmed | refuted — with evidence when run>
```

## Naming and linking

- File names are kebab-case and stable: `inventory/invoice-calculator.md`. Do not rename a
  concept when its title changes; rename only when the underlying asset is renamed.
- One directory holds one slug namespace. `flows/` holds Entry Point, Flow, and Integration
  Boundary concepts; `questions/` holds Open Question and Validation Experiment concepts.
  Suffix by concept kind when two would collide: `invoice-creation-entry.md`,
  `invoice-creation-flow.md`, `erp-export-question.md`, `erp-export-experiment.md`.
- Link with bundle-absolute paths: `[Invoice Calculator](/inventory/invoice-calculator.md)`.
  Relative links are acceptable inside a sub-bundle.
- Every concept must be reachable from `index.md` or from a parent concept. No orphans.
- One concept per file. If a file grows past roughly 200 lines, split it and link the parts.
- Express relationships in prose around the link ("calls", "owns", "publishes to"); OKF links
  are untyped edges.

## Index and log

Root `index.md`. Subdirectory index files are optional; if you link to one, write it, otherwise
link concepts directly:

```markdown
---
okf_version: "0.2"
---

# Discovery Bundle

* [Charter](charter.md) — destination, scope, constraints, success criteria.
* [Ledger](ledger.md) — shards, depth, coverage, exclusions.
* [System map](system.md) — deployables, data, boundaries, riskiest edges.

# Repositories

* [acme-billing](repos/acme-billing.md) — billing API and workers; owns invoice tables.
* [acme-web](repos/acme-web.md) — customer-facing web application.

# Inventory

* [Invoice Calculator](inventory/invoice-calculator.md) — computes invoice totals and tax.

# Flows and boundaries

* [POST /invoices](flows/post-invoices.md) — primary write path into billing.
* [Invoice creation](flows/invoice-creation.md) — request-to-event path.
* [Billing → ERP (SFTP)](flows/billing-erp-sftp.md) — nightly invoice export.

# Data

* [billing.invoices](data/billing-invoices.md) — system of record for issued invoices.

# Rules, risks, seams

* [Line-level half-up rounding](rules/line-level-half-up-rounding.md)
* [Shared invoice table across three services](risks/shared-invoice-table.md)
* [Billing API façade](seams/billing-api-facade.md)

# Open questions

* [Who owns the nightly ERP export?](questions/erp-export-owner.md)
* [Characterize rounding across 10k historical invoices](questions/characterize-rounding.md) — validation experiment.
```

The slugs above are illustrative; use your real concept slugs. If you write subdirectory
`index.md` files, link those instead of individual concepts.

`log.md` is newest-first, grouped by ISO date:

```markdown
# Discovery Log

## 2026-11-03
* **Creation**: Established charter, ledger, and shard plan for 4 repositories.
* **Update**: Inventory completed for `acme-billing` (SH-001–SH-006).
* **Deprecation**: Retired the duplicate `billing-old` component concept.
```

## Update and merge rules

1. **Match by stable key**, not by title: `repo` + canonical path (+ symbol when needed).
2. **One concept per real asset.** If two shards produce the same component, merge into the
   existing file and keep the stronger evidence; record the weaker observation in the body.
3. **Do not delete.** Set `status: deprecated` and explain in the body.
4. **Conflicts are data.** If two shards disagree, keep both claims with evidence and raise an
   Open Question; do not pick the more plausible one silently.
5. **Bump `generated.at`** on every meaningful edit. Append to `log.md`.
6. **Re-verify, don't assume.** After a code change, re-read the cited lines before keeping
   `verified`. Otherwise mark the concept stale via `stale_after` or the ledger.
7. **No secrets, no personal data.** Record key names and locations only.

## Conformance checklist

- [ ] Every non-reserved `.md` file starts with frontmatter containing `type`.
- [ ] Root `index.md` declares `okf_version: "0.2"`.
- [ ] `index.md` and `log.md` follow the section/date formats.
- [ ] Every concept has `generated`; concepts making factual claims have at least one
      `sources` entry.
- [ ] `repo://` sources carry matching `repo` and `commit` fields — at the concept level when
      all sources share a repository, otherwise on each source — or use a resolvable URL.
- [ ] No concept claims `verified` without a recorded check; `verified` is a `{ by, at }` event,
      never a bare `true`.
- [ ] Links resolve, or are intentionally forward references to concepts still to be written.
- [ ] Coverage and exclusions are stated in `ledger.md`.
