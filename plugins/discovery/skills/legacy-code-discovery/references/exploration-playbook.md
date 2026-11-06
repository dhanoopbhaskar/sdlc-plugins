# Exploration Playbook

How to read an unfamiliar codebase efficiently. This is the craft layer under the phases:
hypothesis-driven, boundary-first, and budgeted.

## Read in this order

1. **Intent** — README, docs, ADRs, CONTRIBUTING, issue templates. What is this supposed to be?
2. **Entry** — the process start, routes, CLI, jobs, consumers. Where does work enter?
3. **Configuration** — environment keys, feature flags, deployment config. What changes per
   environment or tenant?
4. **Data shapes** — schemas, DTOs, models, contracts. What are the nouns?
5. **Tests** — what behavior is pinned, and what is conspicuously untested?
6. **Core logic** — only now, the implementation behind the boundaries you have mapped.

Reading core logic first feels productive and produces detailed knowledge of the least
consequential lines. Boundaries carry most of the migration risk.

## Hypothesis-driven loop

```
observe  → form one falsifiable hypothesis → find the cheapest check → update the map
```

Examples:

- Observe a folder named `billing-v2`. Hypothesis: two billing implementations coexist.
  Check: routes and DI registration for both, deployment config, commit dates.
- Observe a table written by three services. Hypothesis: shared integration database.
  Check: write sites, transaction boundaries, who reads it.
- Observe a disabled feature flag near a branch. Hypothesis: dead but load-bearing behavior.
  Check: flag defaults per environment and current values if observable.

One hypothesis at a time, with a check that could fail. Do not collect interesting facts
without a question they can answer.

## Search strategy

Use the strongest search for the question:

| Question | Search |
| --- | --- |
| Where is this defined? | Symbol/definition search, go-to-definition, indexer |
| Who calls this? | Reference search, call hierarchy, graph query |
| Where is this configured? | Config keys, env var names, deployment manifests |
| Where is this string used? | Literal search across first-party code and config |
| Where does this data go? | Table/column names, ORM mappings, SQL, migrations |
| Is this dead? | References from routes, DI, build, deploy; commit history |
| When did this change? | `git log`, blame, diff of the introducing commit |

Rules:

- Exclude dependencies, build output, and generated trees from literal searches.
- A string match is a lead, not a dependency. Confirm with an import, registration, or call.
- Search for the **absence** too: no tests, no config, no owner, no migration.
- Record the query and the path when a result becomes evidence.

## Git archaeology

Version control is the cheapest source of intent:

- `git log --follow <path>` — was this file moved, renamed, or rewritten?
- `git log -S '<symbol>'` — when was this behavior introduced or removed?
- Churn per path — high churn plus high fan-in is a risk hotspot.
- Blame around a suspicious branch — the commit message often names the incident or customer.
- Deleted files and abandoned branches — a previous migration may have started and stopped.
- Tags and release branches — what is actually deployed, versus what is on the default branch.

Treat commit messages as evidence of intent, not proof of current behavior.

## Reading a file you have never seen

1. Read the imports/includes: they reveal the neighbors and the framework.
2. Read the public surface: exported functions, classes, routes, handlers.
3. Read the data structures: they encode the domain.
4. Read error paths and edge cases: they encode the real rules.
5. Read tests before the body when tests exist; they state expected behavior compactly.
6. Skim the middle; do not read line by line unless the behavior is load-bearing.

Timebox: if a file has not yielded a claim, a dependency, or a question after a few minutes,
record why and move on. "Read but found nothing relevant" is a valid note.

## Legacy patterns to recognize

| Pattern | What it often means |
| --- | --- |
| Two implementations of the same rule | Partial migration or tenant-specific behavior |
| Feature flags with no owner | Dead code risk or environment-specific behavior |
| Comments that contradict code | Behavior changed; the comment did not |
| Magic constants and duplicated literals | Undocumented business rules |
| Huge conditional blocks by tenant/region | Configuration encoded in code |
| `catch` that swallows errors | Silent partial success; check downstream effects |
| Retry loops without idempotency | Duplicate side effects under failure |
| Manual SQL strings beside an ORM | Bypassed invariants and hidden dependencies |
| Disabled tests or `skip` markers | Behavior that is no longer verified |
| Copy-pasted utility modules | Divergent behavior with a shared name |
| Build scripts that patch generated code | Hidden source of truth |
| README commands that no longer work | Documentation drift; verify against CI |

## Keep a running question log

While exploring, maintain a list:

```
- Q: Does the nightly export include refunds? | blocks: data migration | default: yes | check: query/report owner
- Q: Is the legacy endpoint still called by mobile? | blocks: contract removal | default: yes | check: gateway logs
```

Every entry needs a blocking decision, a default assumption, and a cheap check. At the end of
the session, move them into `questions/` concepts so the next session inherits them.

## Stop rules

Stop exploring a branch of the code when:

- You can state its responsibility, public surface, and dependencies with evidence.
- Further reading only produces links to concepts already recorded.
- The remaining questions need an owner, runtime data, or an experiment — not more code.
- The budget for the shard is exhausted. Record coverage and mark it `partial`.

## Anti-patterns

- Reading files alphabetically or in directory order.
- Reading everything in a folder because one file was interesting.
- Trusting names, comments, or documentation over code paths.
- Building a mental model without writing concepts down.
- Deep-diving a low-risk module because it is pleasant to read.
- Treating a successful build as evidence of correct behavior.
- Concluding "nothing else calls this" after one search that excluded a whole language or repo.
