# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-11-06

### Added
- `merge-gate` skill: a four-phase review (scope, proof, attack, merge) with three disjoint
  lenses (side effects, security, blast radius) and a computed `sdlc.verdict/v1` verdict.
- Full `merge-gate` reference set: scope resolution and diff hashing, proof receipts and
  regression evidence, isolation modes and briefs, merge and risk-acceptance rules, the
  evidence format, and the base-profile trust boundary.
- `evals/verdict.py` and tests: validate a verdict artifact and recompute its verdict,
  including redaction, risk acceptance, coverage-gap promotion, and verdict arithmetic.
- 11 development fixtures under `evals/fixtures/m2/`: eight defect fixtures across Python,
  TypeScript, Go, and YAML, plus three integrity fixtures (prompt injection, profile
  tampering, weakened assertions). Each fixture has a before/after pair, an applying diff,
  a reference verdict, and a machine-readable expectation file.
- `evals/run.py`: Gate A (format and arithmetic, runs in CI), Gate B (integrity, fails on any
  unsafe pass), and Gate C (held-out recall with per-tier thresholds). Gate B has a committed
  single-context self-run; Gate C takes a held-out score file that is never committed.
- `evals/measure.py`: estimates the always-on core description budget and the static
  per-run gate budget; CI fails when either target is exceeded.
- Profile contract checking in the validator, with a committed sample profile.
- Committed gstack inventory summary so a fresh session does not depend on local files.

### Changed
- The repository is now a marketplace of two plugins instead of a single plugin:
  `sdlc` (`sdlc-behavior-principles`, `merge-gate`, `verify-task`) and
  `discovery` (`repo-reconnaissance`, `system-cartography`, `migration-seams`,
  `legacy-code-discovery`, `code-documenter`).
- Plugin names shortened: `sdlc-core` → `sdlc` and `sdlc-discovery` → `discovery`.
  Plugin directories, manifests, marketplace sources, install commands, docs, and tests
  follow the new names.
- `scripts/validate_skills.py` is multi-root: it validates every `plugins/*/plugin.json`
  and `skills/` tree, cross-checks marketplace entries against plugin roots, enforces
  lockstep versions across plugins, and validates the committed profile and verdict samples.
- `tests/test_validate_skills.py` now covers multi-root discovery, marketplace
  cross-references, lockstep versions, duplicate skill names across plugins, and the
  profile contract.
- CI now runs the validator, Gate A, the context-budget check, and both test suites.
- README documents per-plugin installation, the `sdlc` vs `sdlc` + `discovery` decision,
  the three eval gates, and the context-budget check.
- Version `0.2.1` → `0.3.0`, lockstep across both plugins and the marketplace metadata.

### Removed
- Root `plugin.json` and `mcp.json`; the repository root is no longer a plugin.
- The old single-plugin marketplace entry.

### Migration
- Replace `copilot plugin install sdlc-plugins@sdlc-plugins` with
  `copilot plugin install sdlc@sdlc-plugins`, plus
  `copilot plugin install discovery@sdlc-plugins` when discovery work is needed.
- `verify-task` is **kept** standalone. It was not absorbed into `merge-gate`; the gate
  consumes its five evidence items in Phase 2.

## [0.2.1] - 2026-11-04

### Fixed
- Evidence grading: behavioral claims now require `confirmed` evidence, and `corroborated`
  behavior is recorded as a hypothesis with a Validation Experiment instead of settled
  behavior. Process documents are graded by their weakest planning claim, so
  `evidence: confirmed` no longer appears alongside unknown or blocked work.
- OKF output contract: `charter.md`, `ledger.md`, and `system.md` link to sourced concepts
  instead of carrying `sources`; parent owns `system.md` frontmatter, and `okf-bundle.md` is
  the single source of truth for section ownership.
- `repo://` evidence: resolution clarified across Git hosts with path percent-encoding,
  host-specific line-range anchors (GitHub, GitLab, Bitbucket, Azure DevOps), and
  snapshot-SHA or path-only `inferred` evidence for dirty working trees.
- Validation: link checks now verify heading anchors, scanning ignores indented code blocks
  and HTML comments, version metadata must be semantic versioning, and `check_versions` /
  `check_actor_versions` report non-object JSON and malformed manifests instead of raising
  `AttributeError`.
- Tests: added a minimal OKF bundle fixture and conformance test covering frontmatter, links,
  `repo://` evidence, actors, status values, process-document sources, index/log
  completeness, and a cross-repository Flow with per-source `repo`/`commit` fields.
- Discovery workflow: skills need read access to targets and write access only to the bundle;
  `flows/` is required only when entry points exist; open questions and risks must be
  answered and linked; editing a concept clears `verified` and returns it to `status: draft`,
  including when `migration-seams` adds a parity-hazard section.
- Orchestration: the worker output contract is depth-aware with `system.md` fragment returns
  and parent/worker lease ownership; ledger writes follow a single-writer protocol; added
  behavior/rules and synthesis phase gates plus a final ledger reconciliation gate.
- Depth: a small-estate path uses a single `inventory` shard, while Flows and Integration
  Boundaries stay `deep` artifacts with Open Questions at `inventory`; `system-cartography`
  and Step 2 gates are depth-aware so `inventory` passes are not held to `deep`
  requirements. Standalone phases create a minimal charter (partial bundle) and a `repos/`
  registry, or record its absence as an Open Question.
- Templates: added a `# Coupling` section owned by `migration-seams`, an Owner column and
  atomic groups in `system.md` sequencing, `shard` in the risk example, a defined shard
  `Evidence` column, and fixture/test-data exclusions.
- Reconnaissance: commands redact credentials from remote URLs and use `grep -r` with
  dependency/build-directory exclusions; added `justfile`/`Taskfile` detection, reduced
  non-git census noise, and recorded only measurable coverage rows while marking later-phase
  rows `not yet measured`.
- Phase descriptions gained trigger-precedence notes so multi-phase requests select the
  orchestrator, and are clarified as `legacy-code-discovery` phases.

## [0.2.0] - 2026-11-03

### Added
- `legacy-code-discovery` orchestrator skill for migration-oriented, evidence-graded discovery
  of legacy systems, with an OKF v0.2 output contract.
- `repo-reconnaissance` skill: topology, stack detection, build/run/entry points, deployables,
  exclusions, and shard planning for large repositories.
- `system-cartography` skill: components, typed dependency edges, entry points, flows,
  integration boundaries, and data ownership.
- `migration-seams` skill: risk scoring, coupling and parity analysis, migration options, seams,
  readiness, and slice sequencing.
- Discovery reference library: OKF bundle templates, scale and fan-out rules, question bank,
  detection signals, portable commands, the exploration playbook, and the risk model.
- Readiness, migration-option, and sequencing sections in the `System` template, and a
  parity-hazard variant of the `Business Rule` template.
- `scripts/validate_skills.py`, `tests/test_validate_skills.py`, and a CI workflow that validate
  skill frontmatter, naming, links, manifest shape, generated-actor versions, and repository
  version metadata.

### Changed
- Plugin version bumped to 0.2.0.
- `code-documenter` now clears `verified` when regeneration changes a concept, so human-review
  metadata cannot outlive the content it verified. Incremental updates preserve `verified` only
  when the body and cited sources are unchanged.
- Discovery skill descriptions were narrowed and given compatibility notes to reduce trigger
  overlap and clarify co-installation.
- Read-only, write-target, production-data, and experiment-approval rules were made explicit
  and consistent across the discovery skills.
- `migration-seams` now assesses migration options per deployable and atomic group, with
  readiness, options, and sequencing recorded in `system.md`.
- `code-documenter` now documents when `stable` is appropriate; discovery keeps decision-critical
  concepts at `draft` until human review.
- Shard sizing and lease guidance now live in the reference files, with the skills linking to
  them.

### Fixed
- Reconnaissance: workspace-root detection, census recipes (including untracked and extensionless
  files), manifest and lockfile coverage, and secret-safe search hygiene.
- Cartography: dependency-resolution and evidence grading, flow and data-ownership guidance, and
  the `Integration Boundary` gate.
- Bundle and ledger: required `index.md`/`log.md`, `repo://` evidence conventions, per-source
  `repo`/`commit` for cross-repository citations, worker versus parent ledger ownership,
  `status` versus `verified`, `sources` only for factual claims, and the local checkout root
  recorded in the ledger.
- Templates: `status: draft` on every concept, `<writer>/<version>` actors, `repos/` and `data/`
  index sections, a `# Stack and topology` System section, explicit `system.md` section
  ownership across phases, and behavior-bearing golden files retained as evidence.
- Validator: dependency-free frontmatter parsing with quoted/block scalars and duplicate-key,
  nested-value, multi-line, and tab-indentation rejection; link and image checks including
  images nested in links, bundle-absolute OKF links, angle-bracket destinations, reference
  definitions, and tilde/longer-backtick fences; manifest-shape and generated-actor version
  checks; guarded changelog reads; rejection of empty or whitespace-only `compatibility`
  values; and expanded tests.
- Discovery bundle templates now record repository identity, build/run commands, deployment
  surface, the full coverage vector, shard notes, and generated-code inventory; standalone phase
  skills link new concepts and log entries, and standalone resumes verify the charter scope.

## [0.1.0] - 2025-09-18

### Added
- Initial project structure
