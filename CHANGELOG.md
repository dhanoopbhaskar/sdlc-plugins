# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-11-04

### Fixed
- Aligned evidence grading across the discovery skills: behavioral claims now require
  `confirmed` evidence, and `corroborated` behavior is recorded as a hypothesis with a
  Validation Experiment rather than as settled behavior.
- Clarified that discovery skills need read access to the targets and write access only to the
  bundle, that `flows/` is required only when entry points exist, and that open questions and
  risks are answered and linked rather than asserted.
- Link validation now checks heading anchors, and the minimal OKF fixture test checks titles,
  descriptions, and the required charter/ledger sections.
- Reconnaissance commands now redact credentials from remote URLs before display and use
  `grep -r` (not symlink-following `-R`) with dependency/build-directory exclusions.
- Discovery update rules now clear `verified` and return a materially edited concept to
  `status: draft`, matching the `code-documenter` lifecycle policy. Added the same rule where
  `migration-seams` enriches an existing Business Rule with a parity-hazard section.
- Process documents are graded by their weakest planning claim; the ledger example and templates
  no longer claim `evidence: confirmed` while unknown or blocked work remains.
- Added fixture/test-data exclusions to the ledger template, defined the shard `Evidence` column,
  and distinguished shard state from a concept's OKF lifecycle `status`.
- Clarified `repo://` resolution across Git hosts and added path percent-encoding guidance.
- Added phase gates for behavior/rules and synthesis, and a final ledger reconciliation gate.
- Made the worker output contract depth-aware, added `system.md` fragment returns, and assigned
  lease ownership between the parent and workers.
- Validator `check_versions` and `check_actor_versions` now report non-object JSON and malformed
  manifest shapes instead of raising `AttributeError`; added coverage for those cases.
- Added a minimal OKF bundle fixture and a conformance test covering frontmatter, links,
  `repo://` evidence fields, index/log completeness, and sourced concepts.
- Added a lightweight small-estate path and clarified file-level versus claim-level evidence.
- Clarified that process and aggregate documents (`charter.md`, `ledger.md`, `system.md`) link
  to sourced concepts instead of carrying `sources`, and assigned parent ownership of
  `system.md` frontmatter.
- Standalone phase use now creates a minimal charter and labels the bundle partial.
- Recorded atomic groups in `system.md` `# Sequencing`, added `shard` to the risk example, and
  clarified phase descriptions as `legacy-code-discovery` phases.
- Fixed the `grep -R` typo and aligned secret-file exclusions in the portable commands; added
  `justfile`/`Taskfile` detection and reduced non-git census noise.
- Aligned the depth contract: small estates use one `inventory` shard, Flows and Integration
  Boundaries are `deep` artifacts with Open Questions at `inventory`, and the Step 2 gate no
  longer requires deep work.
- Standalone phase use now creates the multi-repo `repos/` registry, or records its absence as an
  Open Question.
- Defined a single-writer ledger protocol: the parent sets `in-progress`, `done`, and coverage
  totals; workers update `Notes`, lease fields, and `partial`.
- Added an Owner column to the `system.md` sequencing template and the corresponding completion
  gate.
- Reconnaissance completion now records only the coverage rows it can measure and marks
  later-phase rows `not yet measured`.
- Extended the OKF fixture test to check generated actors, evidence and status values,
  process-document sources, and index reachability.
- Made the `system-cartography` completion gate depth-aware, so an `inventory` pass no longer
  has to satisfy `deep` flow and boundary requirements.
- Added a `# Coupling` section to the `System` template and assigned it to `migration-seams`,
  giving the required coupling analysis a concrete output location.
- Defined snapshot-SHA or path-only `inferred` evidence for dirty working trees, so `repo://`
  line ranges never point at a clean commit.
- Documented host-specific line-range anchors for GitHub, GitLab, Bitbucket, and Azure DevOps
  instead of copying GitHub's fragment to every host.
- Made `okf-bundle.md` the single source of truth for `system.md` section ownership and linked
  the phase skills to it.
- Added trigger-precedence notes to the phase descriptions so multi-phase requests select the
  orchestrator.
- Validator link scanning now ignores indented code blocks and HTML comments; version metadata
  must be semantic versioning.
- The OKF fixture now covers a cross-repository Flow with per-source `repo`/`commit` fields and
  nested-index reachability.

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
