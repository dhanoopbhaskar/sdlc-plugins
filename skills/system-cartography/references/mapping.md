# Mapping Methods

Cartography is mostly disciplined evidence collection. Use the strongest available source,
record which one you used, and never upgrade a heuristic to a fact.

## Dependency resolution levels

| Level | Evidence | Grade | Use |
| --- | --- | --- | --- |
| Resolved | Compiler, package manager, or module resolver output | `confirmed` | Build the real graph |
| Declared | Manifest, project file, IDL, schema | `confirmed` for intent | Cross-check against resolved |
| Source-level | Import/include/using statements, DI registration, autoload config | `confirmed` for compile edges; `corroborated` for runtime edges until configuration or execution agrees | Fill gaps; validate on risk |
| Heuristic | String references, naming, comments | `inferred`; `corroborated` only with a second independent signal | A lead, not a dependency |
| Dynamic | Reflection, service discovery, runtime config, convention-based loading | `unknown` until observed | Open question or runtime experiment |

A declared dependency that the resolver does not show may be unused, optional, or supplied at
runtime. That discrepancy is a finding.

## Extraction by artifact

### Package and build metadata

- Read every manifest and lockfile for the shard's units.
- Prefer workspace/project graphs over directory scanning.
- Distinguish direct from transitive dependencies; record versions and major-version skew.
- Note optional, peer, development, and platform-specific dependencies — they change what must
  exist in the target environment.

### Source-level edges

Search for the ecosystem's import forms, but verify the binding:

- Module imports, `using`/`include`/`require`/`use` statements.
- Fully qualified references that bypass imports.
- Dependency injection and service registration (these often define runtime edges that imports
  do not).
- Plugin, provider, and convention-based discovery.
- Reflection or string-based lookup — always `inferred` until observed.

Do not count a mention in a comment, documentation file, or test fixture as a runtime edge.
Record test-only edges separately.

### Runtime edges

Look for outbound calls and their configuration:

- HTTP/gRPC/SOAP/GraphQL clients and generated stubs.
- Base URLs, service names, DNS names, and environment-specific endpoints.
- Message producers and consumers, topic/queue names, routing keys.
- Database connection factories and repository registrations.
- File, SFTP, object storage, and email integrations.
- Cache clients and search clients.

The configuration often reveals edges the code hides: a shared connection string or topic
name is a dependency even if no import exists.

### Contracts

- API specifications (`openapi`, `swagger`, `*.proto`, `*.graphql`, `*.avsc`, AsyncAPI).
- Shared client libraries published from another repository.
- Schema migrations and database DDL.
- File format definitions and export templates.
- Webhook payload definitions.

Record the contract's location, version, and consumers. A contract with no version is a
migration risk.

### SQL and data dependencies

- Views reference tables; procedures reference tables and other procedures; triggers reference
  tables; foreign keys reference tables.
- Application code references tables through ORM mappings, raw SQL, or stored procedure calls.
- Reports and ad hoc queries are consumers even if they live outside the repository.
- Search for table and column names across the shard, but confirm the reference is executable.

### Infrastructure as code

- Resource references, module calls, and variable wiring reveal runtime topology.
- Environments usually differ by variables, not by code; read the variable definitions.
- Managed services declared in IaC are dependencies even if the application treats them as
  transparent.

## Tracing a flow

Use a bounded queue, not open-ended exploration:

```
frontier = [entry point handler]
visited = set()
while frontier and steps < budget:
    node = pop(frontier)
    record node (component, file, line)
    for effect in effects(node):
        if effect is a write/event/call: record it
        if effect crosses a component boundary: add target to frontier
    for failure path in handlers(node): record it
```

Stop when the path leaves the estate, enters third-party code, or exceeds the step budget.
Record the stop reason. A flow that ends in "unknown" is more honest than a flow that invents
a plausible ending.

For each step, capture:

- Component and handler.
- Input and output shape.
- Sync or async.
- Transaction boundary.
- Failure behavior and whether it is retried or compensated.
- Data read/written.

### Async flows

Trace producer → broker → consumer separately. Capture:

- Topic/queue name and schema, including versioning.
- Ordering guarantee (or absence).
- Delivery semantics: at-most-once, at-least-once, exactly-once claim.
- Idempotency key and deduplication.
- Retry policy, backoff, dead-letter destination, replay procedure.
- Consumer group and scaling behavior.

These properties are rarely documented and frequently assumed. Mark assumptions as open
questions.

## Data ownership

For every store and table, classify:

| Pattern | Evidence | Migration implication |
| --- | --- | --- |
| Single writer, multiple readers | One component writes; others read | Easiest to extract; readers need a view or API |
| Single writer, exclusive reader | One writer and one reader | Can move together as a unit |
| Multiple writers | More than one component writes | Needs a ownership decision before cutover |
| Shared integration database | Several deployables read/write by design | Hardest; usually an anti-corruption layer |
| Read-only replica / export | Reporting or analytics consumer | Can lag; check freshness requirements |
| Unknown | No clear write site found | Open question; do not guess |

Count write sites, not mentions. A repository class that only reads is a reader even if it
lives in the same package as the writer.

## Coupling signals you can compute cheaply

- **Fan-in**: number of components that depend on this one. High fan-in means high blast radius.
- **Fan-out**: number of dependencies. High fan-out means many failure modes and version pins.
- **Cycles**: strongly connected groups that must move together or be broken first.
- **Shared data count**: number of other deployables touching the same store.
- **Cross-deployable calls**: runtime edges that cross a release boundary.
- **Duplicated logic**: same rule implemented in more than one component.
- **Version skew**: multiple major versions of a shared dependency in one estate.
- **Test isolation**: components with no runnable tests and no contract tests.

These are enough to rank migration order without a full static-analysis platform.

## Confidence rubric

| Question | Confirmed | Corroborated | Inferred |
| --- | --- | --- | --- |
| Does A depend on B? | Resolver, executed call, or a direct import shows a compile edge | Import plus runtime configuration or registration agree | Only a name, comment, or string match |
| Is this an entry point? | Route/handler or runtime registration read | Route declared and handler found nearby | Naming convention only |
| Who owns this table? | Write sites enumerated and consistent | One writer plus deploy config agrees | Package naming suggests it |
| Is this rule real? | Code path plus test or observed output | Code path plus fixture | Comment or identifier only |

A behavioral claim needs `confirmed` evidence before it appears in a component's behavior section;
`corroborated` behavior is a hypothesis that belongs in `questions/` with a Validation Experiment.
A dependency edge may be recorded as `inferred` or `corroborated` when the signals justify it, but
a material inferred edge also needs an Open Question or validation experiment until evidence
raises it to `confirmed`.

## Sampling rules

When a shard is too large:

- Sample by layer: one representative API, domain, data, job, and UI path.
- Weight toward high churn, high fan-in, and recent change.
- Always read boundaries and configuration in full; behavior concentrates there.
- Record the sample: which files, why, and what remains unread.
- Mark the shard `partial` in the ledger.

Never let a sample be described as a census.
