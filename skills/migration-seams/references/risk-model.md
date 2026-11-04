# Risk, Seam, and Sequencing Model

## Risk taxonomy

| Category | Typical risks | Evidence to look for |
| --- | --- | --- |
| Data | Shared writers, unclear ownership, no constraints, orphaned rows, retention gaps | Write sites, DDL, triggers, reports |
| Behavior | Undocumented rules, rounding, time zones, null/empty semantics, ordering | Code paths, fixtures, golden files |
| Contract | Unversioned APIs, implicit consumers, shared schemas, file formats | Specs, client code, consumer lists |
| Runtime | Untestable environment, missing build, hidden runtime dependency, native library | CI, container, startup config |
| Coupling | Cycles, god modules, cross-deployable transactions, duplicated logic | Dependency graph, churn |
| Integration | Third-party limits, credentials, batch windows, partner change control | Client config, schedules, runbooks |
| Security | Auth enforcement in the wrong layer, secrets in code, tenant isolation | Middleware, config, tests |
| Operations | No observability, manual cutover steps, undocumented runbooks | Logs, metrics, docs |
| Organization | No owner, contested ownership, team capacity, competing priorities | CODEOWNERS, commits, charter |
| Compliance | Data residency, audit trails, retention, licensing | Docs, config, legal constraints |

A risk statement is a sentence with a cause and a consequence. "Legacy invoicing" is a topic.
"Three services write `billing.invoices`, so no service can be cut over independently" is a
risk.

## Scoring anchors

Score each dimension 1–5 using these anchors. Write the rationale next to the score.

### Likelihood

| Score | Anchor |
| --- | --- |
| 1 | Directly contradicted by evidence; will not occur. |
| 2 | Unlikely; requires an unusual condition. |
| 3 | Plausible; has happened elsewhere or depends on an unknown. |
| 4 | Likely; the condition is present and common. |
| 5 | Already occurring or guaranteed by the current design. |

### Impact

| Score | Anchor |
| --- | --- |
| 1 | Cosmetic; no data or user impact. |
| 2 | Local rework; contained to one component. |
| 3 | Schedule slip or degraded behavior for one flow. |
| 4 | Data loss or corruption, outage, or major rework. |
| 5 | Regulatory breach, financial loss, irreversible data damage, or unsafe behavior. |

### Detectability

| Score | Anchor |
| --- | --- |
| 1 | Caught by an existing test or alert before release. |
| 2 | Caught in staging or a canary. |
| 3 | Caught within hours in production by monitoring. |
| 4 | Found by users or reconciliation; days later. |
| 5 | Silent; may never be found or only during an audit. |

Priority = likelihood × impact × detectability (1–125). Bands are a communication aid, not a
decision rule:

| Band | Range | Interpretation |
| --- | --- | --- |
| Critical | 60–125 | Needs a mitigation or explicit acceptance before cutover. |
| High | 30–59 | Must have an owning decision and an early-warning signal. |
| Medium | 12–29 | Track; mitigate if cheap. |
| Low | 1–11 | Note and move on. |

Never let a band hide a dimension. A 5×5×1 risk (likely, high impact, easy to detect) and a
1×5×5 risk (rare, silent, catastrophic) both land in the Medium band, but for different reasons:
the first needs mitigation before cutover, the second needs an early-warning signal and an
explicit acceptance. The band is a starting point, not a decision. The discrimination check in
`migration-seams` counts both Critical and High.

## Seam selection

Score each candidate 1–5 on the criteria, then look for the highest total with no weak
prerequisite. Do not trade away test coverage for speed.

| Criterion | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Contract stability | Undocumented, changing | Documented, some implicit consumers | Versioned, explicit consumers |
| Test coverage | None | Partial or flaky | Behavior pinned by tests |
| Observability | Blind | Logs only | Metrics, traces, alerts |
| Data ownership | Shared writers | Read-only sharing | Single owner |
| Blast radius | Estate-wide | Multiple teams | One team |
| Reversibility | One-way | Manual rollback | Instant routing switch |

If any of contract, test, or observability is 1–2, the seam is not ready. Pick a different
first slice or invest in the prerequisite.

## Parity hazard checklist

Use this as a prompt during behavior extraction. Every item is a place where a reimplementation
can differ without anyone noticing. Record confirmed hazards with the parity-hazard variant of
the Business Rule template in
[`legacy-code-discovery/references/okf-bundle.md`](../../legacy-code-discovery/references/okf-bundle.md).

**Numbers**

- Rounding mode (half-up, half-even, truncate) and where it is applied.
- Decimal vs binary floating point; precision and scale.
- Currency conversion source, rate date, and rounding order.
- Integer division, overflow, and negative-number handling.
- Percentage and tax calculation order.

**Time**

- Input date formats and ambiguous formats (`01/02/2024`).
- Time zone source (server, user, tenant), DST transitions, and stored offset vs UTC.
- Week start, fiscal calendars, leap years, and month-end rules.
- Precision truncation (seconds, milliseconds, microseconds).
- Clock source and skew assumptions.

**Text**

- Collation and sort order; case-sensitive vs case-insensitive comparison.
- Unicode normalization and grapheme handling.
- Trimming rules, empty string vs null, and default values.
- Encoding, byte-length limits, and truncation behavior.
- Identifier case sensitivity in the data store.

**Identity**

- Key generation strategy, sequence resets, and collision handling.
- Case sensitivity and normalization of identifiers.
- UUID/ULID format, version, and time component.
- Composite keys, natural vs surrogate keys, and soft-delete uniqueness.

**State and concurrency**

- Allowed state transitions and their guards.
- Optimistic vs pessimistic locking and isolation level.
- Retry semantics, idempotency keys, and duplicate suppression.
- Event ordering and at-least-once delivery handling.
- Soft delete and audit trail behavior.

**Errors**

- Exception-to-status mapping and error body shape.
- Partial success and batch error handling.
- Retryable vs non-retryable classification.
- Silent fallbacks and default-on-failure behavior.

**Security**

- Where authentication is enforced and what it trusts.
- Authorization model (role, attribute, tenant) and default-deny behavior.
- Session, token, and cookie lifetime and renewal.
- Secret rotation and encryption at rest/in transit.

**Integration**

- Header, content-type, and encoding conventions.
- Pagination, filtering, and sorting semantics.
- Timeout, retry, and rate-limit behavior.
- Certificate, TLS, and proxy assumptions.
- File naming, delimiter, and batch layout.

**Operations**

- Batch windows and file-locking assumptions.
- Startup order and readiness dependencies.
- Graceful shutdown, in-flight work, and cache warmup.
- Manual runbooks and replay procedures.

## Atomic groups

Some components cannot be migrated independently. Group them when any of these is true:

- They share a database with more than one writer and no clean interface.
- One logical transaction spans them.
- They share an in-process contract that cannot be versioned.
- They share mutable configuration that selects behavior.
- A synchronous call chain has no timeout or fallback, so partial migration creates a hard
  dependency.

Compute groups by starting from shared-data and transaction edges, not from calls. Call edges
can usually be strangled; shared writes usually cannot.

Within a group, identify the smallest slice that can be extracted first (often a read path, a
report, or a single entry point) and what must remain together until the group is broken.

## Sequencing algorithm

1. Build the dependency graph (component → component) with edge types.
2. Collapse shared-data and cross-transaction edges into atomic groups.
3. Detect remaining cycles. Collapse strongly connected components into sequencing groups, or
   specify cycle-breaking prerequisites; topologically sort only once the resulting graph is
   acyclic.
4. Within each rank, order by ascending blast radius and ascending readiness cost.
5. Pull forward any slice that de-risks a top-three risk, even if it is not the easiest.
6. Verify the first slice produces an observable end-to-end outcome.
7. For each slice, record: proves, does not prove, rollback, prerequisites, owner.

The result is a candidate order, not a commitment. Mark it `draft` until the prerequisites are
confirmed.

## Readiness rubric

| Level | Build | Run | Test | Observe | Document | Data | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Strong | Clean build in CI | Reproducible locally | Suites run without prod secrets | Metrics + traces + alerts | ADRs and current runbooks | Single owner | Named team |
| Partial | Builds with manual steps | Runs with shared environment | Some tests, gaps known | Logs only | Partial or stale docs | Read sharing | Informal owner |
| Weak | Broken or undocumented | Cannot run | None or disabled | None | Names only | Multiple writers | None |

A deployable with a `weak` Build or Run dimension is a migration prerequisite, not a candidate.
Treat it the same way when two or more other readiness dimensions are `weak`.

## Migration option comparison

| Option | Evidence that supports it | Evidence that argues against |
| --- | --- | --- |
| Rehost | Runtime compatible; low code change; strong ops maturity | Platform-specific dependencies; licensing traps |
| Replatform | Stable contracts; replaceable runtime pieces | Deep framework coupling; untested behavior |
| Refactor in place | Good tests; clear seams; active ownership | No tests; high coupling; no owner |
| Rewrite | Bounded scope; explicit rules; parallel-run feasible | Unbounded domain; undocumented behavior; data gravity |
| Retire | No consumers; replacement exists | Hidden consumers; regulatory retention |

Do not select an option in the abstract. Tie it to specific components and the evidence that
makes it viable there.

## Anti-patterns

- **Risk theater**: long registers with no decisions, owners, or early warnings.
- **Uniform severity**: everything is high, so nothing is.
- **Effort as risk**: "it's a lot of work" is a schedule concern, not a migration risk.
- **Seam by architecture diagram**: seams exist where contracts, tests, and data ownership
  allow them, not where the diagram looks clean.
- **Big-bang by default**: chosen because discovery is incomplete, not because it is safer.
- **Parity by assertion**: "the new stack handles that" without a test or observation.
