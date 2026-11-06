# sdlc-plugins

Software Development Lifecycle (SDLC) plugins for AI coding agents, packaged using the [Agent Plugins](https://agent-plugins.org/) spec (v1.0.0).

This repository publishes two plugins:

| Plugin | What it is for | Skills |
| --- | --- | --- |
| `sdlc` | Day-to-day change work: plan the change, investigate failures, verify completion, and keep diffs honest before merge. | `sdlc-behavior-principles`, `plan`, `merge-gate`, `investigate`, `verify-task` |
| `discovery` | Understanding an unfamiliar or legacy estate before a migration. | `repo-reconnaissance`, `system-cartography`, `migration-seams`, `legacy-code-discovery`, `code-documenter` |

## Which plugins do I need?

- **Installing only one?** Install `sdlc`. It is the smaller, always-useful set and covers the plan → implement → investigate → review → verify loop.
- **Doing migration or due-diligence work?** Install `sdlc` plus `discovery`. The discovery skills produce the evidence bundle; they do not replace the review gate.
- **Want the whole loop?** Install both. `merge-gate` is designed to consume the same evidence vocabulary the other skills produce.

The plugins are versioned in lockstep: one version, one changelog, one release tag.

## Skills

### `sdlc`

| Skill | Description |
| --- | --- |
| [sdlc-behavior-principles](plugins/sdlc/skills/sdlc-behavior-principles/SKILL.md) | Behavioral guardrails for planning, implementing, and reviewing changes: surface assumptions, keep solutions simple, make surgical diffs, require verifiable checks, and confirm destructive operations. |
| [plan](plugins/sdlc/skills/plan/SKILL.md) | Turns a request into a spec with falsifiable acceptance criteria, a risk register, a review tier, and a `.sdlc/profile.json` project profile. Includes an explicit spike mode and an exhaustive `T3` depth with an impact map, approach decision, and blast radius. |
| [merge-gate](plugins/sdlc/skills/merge-gate/SKILL.md) | Reviews a change before merge: scope, proof, three attack lenses, and a computed verdict that never claims merge-ready without evidence. |
| [investigate](plugins/sdlc/skills/investigate/SKILL.md) | Finds and proves a root cause before fixing a failing test, stack trace, or wrong output, then proves the fix with a regression test or an explicit infra proof. |
| [verify-task](plugins/sdlc/skills/verify-task/SKILL.md) | Enforces explicit proof of correctness (requirement, test, regression, diff, unproven) before a task is declared done. |

### `discovery`

| Skill | Description |
| --- | --- |
| [code-documenter](plugins/discovery/skills/code-documenter/SKILL.md) | Generates and maintains [OKF](plugins/discovery/skills/code-documenter/references/SPEC.md)-compliant knowledge bases documenting a codebase's modules, classes, functions, architecture, and configuration. |
| [legacy-code-discovery](plugins/discovery/skills/legacy-code-discovery/SKILL.md) | Orchestrates evidence-graded discovery of a legacy estate before a migration: charter, coverage ledger, phases, gates, and an OKF decision dossier. |
| [repo-reconnaissance](plugins/discovery/skills/repo-reconnaissance/SKILL.md) | Read-only structural survey: repository topology, stacks and versions, build/test/run entry points, deployable units, exclusions, a scalable shard plan, and an emitted or enriched `.sdlc/profile.json`. |
| [system-cartography](plugins/discovery/skills/system-cartography/SKILL.md) | Maps components, typed dependency edges, entry points, end-to-end flows, integration contracts, and data ownership without assuming a tech stack. |
| [migration-seams](plugins/discovery/skills/migration-seams/SKILL.md) | Converts the map into migration decisions: risk scoring, coupling hotspots, behavioral parity hazards, seams, readiness, and slice sequencing. |

The discovery skills are stack-neutral and scale from a single repository to monorepos and multi-repo estates.

## Installation

Add this repository as a plugin source in a client that supports the Agent Plugins spec, then enable `sdlc` and, if needed, `discovery`. Consult your client's documentation for how to register a plugin by Git URL, local path, or repository subdirectory.

### GitHub Copilot CLI

This repository is also published as a [plugin marketplace](.github/plugin/marketplace.json) for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace):

```shell
copilot plugin marketplace add dhanoopbhaskar/sdlc-plugins
copilot plugin install sdlc@sdlc-plugins
copilot plugin install discovery@sdlc-plugins
```

Install `discovery` only when the task is migration or due-diligence work.

## Usage

Once installed, skills are picked up automatically by the agent when their `description` matches the current task—no manual invocation is required. For example:

- Ask the agent to plan, implement, or review a change and it will apply the `sdlc-behavior-principles` guardrails.
- Ask the agent to plan or break down a change and it will use `plan` to write falsifiable acceptance criteria, a risk register, a review tier, and the project profile. Ask for exhaustive analysis on a cross-cutting change and it proposes `T3` with a transitive impact map, an approach decision, and a blast radius.
- Ask the agent to debug a failing test or stack trace and it will use `investigate` to prove the root cause before fixing it.
- Ask the agent to confirm a task is complete and it will apply the `verify-task` checklist.
- Ask the agent to review a diff before merging and it will run `merge-gate`.
- Ask the agent to document a codebase and it will apply the `code-documenter` workflow.
- Ask the agent to map a legacy system before a migration and it will apply `legacy-code-discovery`, scaling its survey with `repo-reconnaissance`, `system-cartography`, and `migration-seams`.

`plan` and `repo-reconnaissance` can create `.sdlc/profile.json`, a committed, user-owned description of the project's stacks, commands, risk paths, and exclusions. `merge-gate` reads it from the base commit and never executes commands that appear only in the reviewed tree.

## Project Structure

```
plugins/
  sdlc/
    plugin.json           # Plugin manifest
    skills/               # Agent Skills, one directory per skill
      <skill-name>/SKILL.md
      <skill-name>/references/  # Supporting material loaded on demand
  discovery/
    plugin.json
    skills/
evals/
  verdict.py              # Validates and recomputes a merge-gate verdict artifact
  investigation.py        # Validates a root-cause investigation report
  run.py                  # Gate A (format), B (integrity), C (recall), D (root cause)
  measure.py              # Estimates install and per-run context budgets
  fixtures/m0/            # M0 prototype fixtures for the gate
  fixtures/m2/            # 8 defect fixtures and 3 integrity fixtures
  fixtures/m3/            # 3 root-cause fixtures with regression tests
  runs/                   # Recorded agent runs used by Gates B and C
  recall/                 # Held-out score format; the held-out set is not committed
scripts/
  validate_skills.py      # Validates skill packaging, links, and version metadata
tests/
  test_validate_skills.py # Tests the multi-root validator
  fixtures/okf-bundle/    # Minimal OKF bundle used by the conformance test
  fixtures/profile/       # Sample .sdlc/profile.json used by the contract check
.github/plugin/
  marketplace.json        # Two plugin entries for GitHub Copilot CLI
.github/workflows/
  validate.yml            # CI validation on push and pull request
CHANGELOG.md              # Lockstep release history
```

## Validation

Run the repository checks locally:

```shell
python3 scripts/validate_skills.py
python3 evals/run.py --gate=a
python3 evals/run.py --gate=d
python3 evals/measure.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s evals -v
```

The script validates every plugin root and skill frontmatter, naming, relative and image links (including
angle-bracket destinations, reference definitions, heading anchors, and bundle-absolute links
inside OKF bundles, while ignoring fenced/indented code and HTML comments), manifest shape,
marketplace cross-references, version lockstep, generated-actor versions, the profile sample
contract, and the committed verdict fixtures.

Gate A checks fixture schema, evidence format, provenance, redaction, and verdict arithmetic
on every committed fixture. Gate B validates recorded integrity runs and fails on any unsafe
pass. Gate D checks the three root-cause fixtures: the reference report names the mechanism,
cites evidence, records the alternatives, and the regression test fails before the fix and
passes after it. Gate C scores a held-out set supplied by the user; the held-out set is never
committed and is not used to tune the gate. The same deterministic checks (validator, Gate A,
Gate D, context budgets, and unit tests) run in CI on every push and pull request.

When bumping the plugin version, update every `plugin.json`, the marketplace metadata and
entries, and any concrete `generated.by` example actors; the validator fails when they drift.

## Contributing

See [CHANGELOG.md](CHANGELOG.md) for release history. Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html) conventions when proposing changes.

## License

[MIT](LICENSE)
