# sdlc-plugins

Software Development Lifecycle (SDLC) plugins for AI coding agents, packaged using the [Agent Plugins](https://agent-plugins.org/) spec (v1.0.0).

## What's Included

This plugin bundles a set of **Agent Skills**—reusable, discoverable instructions that an agent loads on demand based on the task at hand.

| Skill | Description |
| --- | --- |
| [sdlc-behavior-principles](skills/sdlc-behavior-principles/SKILL.md) | Behavioral guardrails for planning, implementing, and reviewing changes: surface assumptions, keep solutions simple, make surgical diffs, and require verifiable checks. |
| [verify-task](skills/verify-task/SKILL.md) | Enforces explicit proof of correctness (requirement, test, regression, diff, unproven) before a task is declared done. |
| [code-documenter](skills/code-documenter/SKILL.md) | Generates and maintains [OKF](skills/code-documenter/references/SPEC.md)-compliant knowledge bases documenting a codebase's modules, classes, functions, architecture, and configuration. |
| [legacy-code-discovery](skills/legacy-code-discovery/SKILL.md) | Orchestrates evidence-graded discovery of a legacy estate before a migration: charter, coverage ledger, phases, gates, and an OKF decision dossier. |
| [repo-reconnaissance](skills/repo-reconnaissance/SKILL.md) | Read-only structural survey: repository topology, stacks and versions, build/test/run entry points, deployable units, exclusions, and a scalable shard plan. |
| [system-cartography](skills/system-cartography/SKILL.md) | Maps components, typed dependency edges, entry points, end-to-end flows, integration contracts, and data ownership without assuming a tech stack. |
| [migration-seams](skills/migration-seams/SKILL.md) | Converts the map into migration decisions: risk scoring, coupling hotspots, behavioral parity hazards, seams, readiness, and slice sequencing. |

The discovery skills are stack-neutral and scale from a single repository to monorepos and
multi-repo estates.

No MCP servers are configured in [mcp.json](mcp.json) at this time.

## Installation

Add this repository as a plugin source in a client that supports the Agent Plugins spec, then enable `sdlc-plugins`. Consult your client's documentation for how to register a plugin by Git URL or local path.

### GitHub Copilot CLI

This repository is also published as a [plugin marketplace](.github/plugin/marketplace.json) for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace):

```shell
copilot plugin marketplace add dhanoopbhaskar/sdlc-plugins
copilot plugin install sdlc-plugins@sdlc-plugins
```

## Usage

Once installed, skills are picked up automatically by the agent when their `description` matches the current task—no manual invocation is required. For example:
- Ask the agent to plan, implement, or review a change and it will apply the `sdlc-behavior-principles` guardrails.
- Ask the agent to confirm a task is complete and it will apply the `verify-task` checklist.
- Ask the agent to document a codebase and it will apply the `code-documenter` workflow.
- Ask the agent to map a legacy system before a migration and it will apply
  `legacy-code-discovery`, scaling its survey with `repo-reconnaissance`,
  `system-cartography`, and `migration-seams`.

## Project Structure

```
plugin.json               # Plugin manifest (required)
mcp.json                  # MCP servers configuration
CHANGELOG.md              # Project changelog
skills/                   # Agent Skills, one directory per skill
  <skill-name>/SKILL.md
  <skill-name>/references/ # Supporting material loaded on demand
scripts/
  validate_skills.py      # Validates skill frontmatter, links, and version metadata
tests/
  test_validate_skills.py # Tests the validator and its frontmatter parser
  fixtures/okf-bundle/    # Minimal OKF bundle used by the conformance test
.github/plugin/
  marketplace.json        # Plugin marketplace manifest for GitHub Copilot CLI
.github/workflows/
  validate.yml            # CI validation on push and pull request
```

## Validation

Run the repository checks locally:

```shell
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests -v
```

The script validates Skill frontmatter, naming, relative and image links (including
angle-bracket destinations, reference definitions, heading anchors, and bundle-absolute links
inside OKF bundles, while ignoring fenced/indented code and HTML comments), manifest shape and
version metadata, and generated-actor versions.
The tests cover the validator, its frontmatter parser, its link, manifest, and version checks,
and a minimal OKF bundle fixture. The same checks run in CI on every push and pull request.

When bumping the plugin version, update any concrete `generated.by` example actors in the
skills; the validator fails when they drift from `plugin.json`.

## Contributing

See [CHANGELOG.md](CHANGELOG.md) for release history. Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html) conventions when proposing changes.

## License

[MIT](LICENSE)
