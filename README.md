# sdlc-plugins

Software Development Lifecycle (SDLC) plugins for AI coding agents, packaged using the [Agent Plugins](https://agent-plugins.org/) spec (v1.0.0).

## What's Included

This plugin bundles a set of **Agent Skills**—reusable, discoverable instructions that an agent loads on demand based on the task at hand.

| Skill | Description |
| --- | --- |
| [sdlc-behavior-principles](skills/sdlc-behavior-principles/SKILL.md) | Behavioral guardrails for planning, implementing, and reviewing changes: surface assumptions, keep solutions simple, make surgical diffs, and require verifiable checks. |
| [verify-task](skills/verify-task/SKILL.md) | Enforces explicit proof of correctness (requirement, test, regression, diff, unproven) before a task is declared done. |
| [code-documenter](skills/code-documenter/SKILL.md) | Generates and maintains [OKF](skills/code-documenter/references/SPEC.md)-compliant knowledge bases documenting a codebase's modules, classes, functions, architecture, and configuration. |

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

## Project Structure

```
plugin.json               # Plugin manifest (required)
mcp.json                  # MCP servers configuration
CHANGELOG.md              # Project changelog
skills/                   # Agent Skills, one directory per skill
  <skill-name>/SKILL.md
.github/plugin/
  marketplace.json        # Plugin marketplace manifest for GitHub Copilot CLI
```

## Contributing

See [CHANGELOG.md](CHANGELOG.md) for release history. Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html) conventions when proposing changes.

## License

[MIT](LICENSE)
