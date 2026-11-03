# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
