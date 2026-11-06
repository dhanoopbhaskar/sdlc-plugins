# DevLoop v1 — Plan (Draft)

> **Status:** draft, not yet approved. Writing of skill text has **not** started.
> **Date:** 2026-11-06
> **Supersedes:** nothing. Companion to `specs/gstack-skills-inventory.md` (local, gitignored).

## 0. Resume here

A fresh session needs only this section plus the files below.

**Read first**

1. `docs/devloop-v1-plan.md` — this document.
2. `specs/gstack-skills-inventory.md` — what we are replacing (local only, gitignored).
3. `skills/verify-task/SKILL.md` — being absorbed into `merge-gate`, not deleted.
4. `skills/sdlc-behavior-principles/SKILL.md` — being extended.
5. `scripts/validate_skills.py` — hardcodes a single plugin root; must change for two plugins.
6. `plugin.json`, `.github/plugin/marketplace.json` — current single-plugin packaging.

**Open decisions — need an answer before Milestone 1**

| # | Decision | Recommended | Alternative |
|---|---|---|---|
| D1 | Name of the merged gate skill | `merge-gate` | `review`, `premerge` |
| D2 | Project profile artifact | `.sdlc/profile.json`, committed | gitignored, or no file (re-probe each run) |
| D3 | Executing discovered commands | Show + confirm once, cache in profile, then run | auto-run, or never run |

If a decision is rejected, record the choice in §11 and update the affected sections.

**Next action after decisions:** Milestone 0 (§8).

---

## 1. Thesis

AI writes code that looks clean and hides side effects. The scarce resource is not generation — it is **trust**. Therefore the product is not "a coding agent" but **a gate that makes a change provable and adversarially reviewed before a human merges it**.

The differentiator is not skill count. It is the depth and honesty of one gate.

**Promise:** *idea → merge-ready*, with evidence the human can audit. Not merged, not pushed, not deployed.

## 2. Scope

### In

- 9 skills, split across 2 plugins.
- One flagship gate that proves correctness and attacks the diff from three independent angles.
- A machine-readable project profile so the skills are genuinely stack-agnostic.
- A planted-defect eval suite that measures the gate.

### Out (explicitly, in writing)

- Code generation, scaffolding, or autonomous implementation loops.
- `ship`, push, merge, deploy, canary, release automation. The loop ends at merge-ready.
- iOS, browser automation, design production, benchmarking, agent orchestration, gstack meta-skills.
- Harness-specific hooks (permission blocking, file-edit interception). Instructions only in v1.
- Language- or framework-specific rules. Everything resolves through the profile.
- Any tool that only works if a specific model is installed.

## 3. Current → target

| | Now | v1 |
|---|---|---|
| Installed gstack skills | 65 | 0 |
| Always-on description tokens (gstack) | ~6,560 | 0 |
| This plugin's skills | 7 (one plugin) | 9 (two plugins) |
| Core-only install description tokens | ~860 | ~225 |
| Plugins | 1 | 2 (`sdlc-core`, `sdlc-discovery`) |

The core-only number is the point: a greenfield user pays ~225 tokens for the full loop and never loads migration/cartography.

### Target skill set

| Plugin | Skill | Status |
|---|---|---|
| `sdlc-core` | `sdlc-behavior-principles` | extended (absorbs destructive-op guard) |
| `sdlc-core` | `plan` | new |
| `sdlc-core` | **`merge-gate`** | new; absorbs `verify-task` |
| `sdlc-core` | `investigate` | new |
| `sdlc-discovery` | `repo-reconnaissance` | extended (emits profile) |
| `sdlc-discovery` | `system-cartography` | unchanged |
| `sdlc-discovery` | `migration-seams` | unchanged |
| `sdlc-discovery` | `legacy-code-discovery` | unchanged |
| `sdlc-discovery` | `code-documenter` | unchanged |

## 4. Architecture

### 4.1 Two plugins, one repo

```
sdlc-plugins/
├── plugins/
│   ├── sdlc-core/
│   │   ├── plugin.json
│   │   └── skills/{sdlc-behavior-principles,plan,merge-gate,investigate}/
│   └── sdlc-discovery/
│       ├── plugin.json
│       └── skills/{repo-reconnaissance,system-cartography,migration-seams,legacy-code-discovery,code-documenter}/
├── evals/
├── docs/
├── scripts/validate_skills.py
└── .github/plugin/marketplace.json   # two entries, source: ./plugins/<name>
```

Agent Plugins v1 requires one `plugin.json` per plugin root, so the repo root stops being a plugin. **M0 must verify that the Copilot CLI marketplace accepts subdirectory `source` values.** If it does not, fallback: two repositories, with this repo as the aggregator marketplace.

### 4.2 The profile contract (glue)

Path: `.sdlc/profile.json`. Written once by `plan` (light probe) or `repo-reconnaissance` (deep survey). Committed by default (D2).

```json
{
  "schema": "sdlc.profile/v1",
  "generated_by": "plan",
  "stack": ["python"],
  "commands": {
    "install":   { "cmd": "uv sync",                 "source": "uv.lock" },
    "test":      { "cmd": "uv run pytest -q",         "source": "pyproject.toml" },
    "lint":      { "cmd": "uv run ruff check .",      "source": "pyproject.toml" },
    "typecheck": { "cmd": "uv run mypy .",            "source": "pyproject.toml" },
    "build":     null
  },
  "ci": { "file": ".github/workflows/ci.yml", "jobs": ["test", "lint"] },
  "risk_paths": ["src/auth/**", "src/payments/**", "migrations/**"],
  "notes": "Tests require DATABASE_URL; use docker compose up -d db"
}
```

Rules:

- Probe order: explicit profile → CI config → manifests (`package.json`, `pyproject.toml`, `go.mod`, `Makefile`, `Cargo.toml`, `pom.xml`, …) → ask.
- Never guess silently. Every command records its `source`.
- Unknown command is `null`, never invented.
- `risk_paths` drives review tiering.
- Editing the profile is always allowed; it is user-owned after creation.

### 4.3 The gate: four phases

```
Phase 1  SCOPE   diff vs base · changed files · AC mapping · profile
Phase 2  PROVE   requirement · tests run · regression · diff justified · unproven
Phase 3  ATTACK  L1 side-effects/state · L2 security/trust · L3 blast radius
Phase 4  MERGE   dedupe · severity · arithmetic verdict · unproven list
```

**Non-negotiables**

1. Phase 2 is complete and frozen before any lens opens.
2. The verdict is arithmetic, not narrated (§4.6).
3. No finding without a concrete trigger (§4.5).
4. The gate always prints what it did not check.

### 4.4 Lens definitions (v0 draft)

These become `references/lens-l1.md`, `lens-l2.md`, `lens-l3.md`. Only the active lens file is read during a pass.

**L1 — Side effects & state**

- Mutable state: writes, deletes, updates; partial writes; multi-step operations without a transaction.
- Ordering and atomicity: commit boundaries, ordering between side effects and responses.
- Idempotency: retries, duplicate delivery, double-submit, at-least-once consumers.
- Error paths: swallowed exceptions, fallbacks that mask failure, cleanup skipped on throw.
- **Dropped guards:** removed or relaxed validation, authz, bounds checks, null checks, feature flags.
- Input edges: empty, null, zero, negative, unicode, very large.
- Concurrency: races, shared caches, TOCTOU, lock scope.
- Resources: unclosed handles, unbounded growth, leaked subscriptions.
- Caching: key composition, invalidation, staleness, tenant/user scoping.
- Tests: deleted or weakened assertions, skipped tests, mocks that hide the real behavior.
- Defaults: silent fallback to an unsafe default; config typos tolerated.
- Time: timezone, clock skew, expiry boundaries.

**L2 — Security & trust boundaries**

- AuthN/AuthZ: present, and enforced *before* the effect; tenant scoping; privilege escalation; IDOR.
- Input validation at the trust boundary; allowlist over denylist.
- Injection: SQL/ORM raw fragments, shell, template, log, header.
- Secrets: hardcoded, logged, in errors, in URLs, in fixtures.
- Crypto: algorithms, randomness, constant-time comparison.
- SSRF, path traversal, open redirect, unsafe deserialization.
- **LLM boundary:** retrieved/tool content treated as instructions; prompt injection; model output trusted as code/SQL/shell; secret exfiltration through tools.
- Dependencies: new package, typosquat, unpinned, postinstall scripts.
- Data exposure: PII in logs/errors/responses; returning more than needed.
- CORS, CSRF, session and cookie flags, cache headers.
- Uploads and archive extraction.

**L3 — Operational blast radius**

- Migrations: forward and rollback, lock time, backfill, nullable/default, table size.
- Backwards compatibility: API, schema, event contracts, consumers.
- Config/env: new required variables, defaults, secret provisioning, per-env drift.
- Feature flags: default state, kill switch, cleanup plan.
- Deploy ordering: code before/after schema; rolling-deploy safety.
- Observability: logs, metrics, traces for new paths; alerting; actionable errors.
- Failure modes: dependency down, timeout, retry storm, circuit breaking.
- Cost: query plans, N+1, storage, egress.
- Data retention and deletion.
- Rollback: can this be reverted without data loss?
- Capacity: indexes, cardinality, quotas.

### 4.5 Evidence format

Every finding:

```
### P0-001 · L1 · src/auth/session.ts:88
Trigger:   request with an expired cookie plus a refreshed token
Consequence: session accepted after expiry (authz bypass)
Fix:       compare exp before issuing the token; add regression test
```

Rules:

- A finding without a concrete trigger is invalid and must be deleted.
- `file:line` is required. Ranges allowed.
- Each lens ends with a **Coverage** block: `checked`, `not applicable`, `could not check`.
- Findings are written to separate artifacts (`l1.md`, `l2.md`, `l3.md`) and merged in Phase 4.

### 4.6 Verdict arithmetic

| Severity | Definition |
|---|---|
| P0 | Data loss, authz bypass, secret exposure, irreversible destructive action |
| P1 | Correctness bug or side effect likely to reach production |
| P2 | Real risk or quality issue with no immediate failure path |
| P3 | Nit, style, naming, non-blocking observation |

```
any P0                         → BLOCK
else any P1                    → FIX
else any UNPROVEN not accepted → BLOCKED-UNVERIFIED
else                           → MERGE-READY
```

`MERGE-READY` is impossible without Phase 2 evidence. "Tests should pass" is a `BLOCKED-UNVERIFIED`, not a pass.

### 4.7 Tiers (depth, not lens count)

All three lenses always run. Depth scales:

| Tier | Triggers | Depth |
|---|---|---|
| T0 | docs, comments, copy, test-only, non-executable config | short checklist per lens |
| T1 | default logic change | full checklist |
| T2 | `risk_paths` match: auth, payments, deletion, migrations, infra, crypto, external IO, concurrency | full checklist + optional second model + human sign-off |

`plan` proposes the tier; `merge-gate` re-derives it from the diff. If they disagree, the higher tier wins.

### 4.8 Blindness mechanics — and the honest limit

- Each pass receives: the diff, the ACs, and its own lens file. Nothing else.
- Findings go to separate artifacts. Prior artifacts are not read until Phase 4.
- If the harness supports isolated sub-sessions, run each lens there (true isolation).
- If not, run sequentially with artifact separation and **state the limitation in the verdict** (`single-context review`). Do not claim three independent reviews you did not perform.

## 5. Skill contracts

Each contract: trigger · input · process · gates · output · failure mode.

### 5.1 `merge-gate` (flagship)

- **Trigger:** "review my diff", "is this done", "ready to merge", "check my work", "before I merge".
- **Input:** branch/diff, ACs from `plan` (or reconstructed), `.sdlc/profile.json`.
- **Process:** §4.3.
- **Gates:** no verdict without Phase 2 evidence; no finding without a trigger; no `MERGE-READY` with unaccepted `UNPROVEN`.
- **Output:** `review/<slug>/` with `scope.md`, `proof.md`, `l1.md`, `l2.md`, `l3.md`, `verdict.md`. Exact location configurable; default under the profile data dir is TBD (D2 follow-up).
- **Failure:** tests cannot run → `BLOCKED-UNVERIFIED` with the exact missing prerequisite; never a soft pass.
- **Size:** SKILL.md ~180 lines; depth in `references/` (cap is 500 lines body).

### 5.2 `plan`

- **Trigger:** "plan this", "spec this", "how should we build", "break this down".
- **Process:** clarify ambiguities (max 3 questions) → spec → ACs as falsifiable statements → risk register → `risk_paths` → proposed tier → bootstrap profile.
- **Output:** `specs/` or issue text (user-chosen) + `.sdlc/profile.json`.
- **Gate:** no plan without testable ACs.
- **Failure:** ambiguity that blocks ACs → stop and ask; do not invent scope.

### 5.3 `investigate`

- **Trigger:** failing test, stack trace, "why does this happen", broken output.
- **Iron law:** no fix before a demonstrated root cause.
- **Process:** reproduce → minimise → isolate → state cause with evidence → fix → prove with a regression test.
- **Output:** cause statement + repro + regression test + diff.
- **Failure:** cannot reproduce → say so and stop; do not guess-patch.

### 5.4 `sdlc-behavior-principles` (extended)

Adds to existing sections:

- **Assume the diff is lying to you.** Clean-looking code is the default, not evidence.
- **Destructive operations require explicit confirmation:** data deletion, force-push, `reset --hard`, dropping tables, bulk updates, dependency removal.
- **Every changed line traces to approved scope**, or it is reverted.

### 5.5 `repo-reconnaissance` (extended)

Adds: emit/update `.sdlc/profile.json` using the same schema and probe order as `plan`.

## 6. Repo changes

| Change | Detail |
|---|---|
| `git mv` 7 skills into `plugins/sdlc-{core,discovery}/skills/` | history preserved |
| Two `plugin.json` files | `sdlc-core`, `sdlc-discovery`, version `0.3.0` |
| Marketplace | two entries; verify subdirectory `source` support |
| `scripts/validate_skills.py` | iterate plugin roots; validate each `plugin.json` + `skills/`; cross-check marketplace |
| `tests/test_validate_skills.py` | update `SKILLS_DIR` monkeypatching; add multi-root cases |
| README | per-plugin install and a decision guide: core vs core+discovery |
| CHANGELOG | breaking: `verify-task` removed (absorbed); migration note |
| Version | `0.2.1` → `0.3.0` (0.x minor may break) |

> Validator constraints to respect in every new skill: name `^[a-z0-9]+(-[a-z0-9]+)*$` ≤64 chars; description ≤1024; body ≤500 lines; links must resolve; actor versions must match the plugin version.

## 7. Eval plan

Location: `evals/` (not shipped in either plugin).

### Fixtures

Five defect repos. Each patch is a plausible refactor that looks clean and hides one defect:

| # | Stack | Planted defect | Lens |
|---|---|---|---|
| 1 | Python | `require_admin` check removed during a refactor | L2 |
| 2 | TypeScript | DB write not awaited before the response | L1 |
| 3 | Go | `NOT NULL` column with no default and no down migration | L3 |
| 4 | Python | Tool output concatenated into the system prompt | L2 |
| 5 | TypeScript | Cache key omits the tenant | L1 + L2 |

Controls: 10 defect-free diffs (5 T0, 3 T1, 2 T2) for false positives. Plus one repo with no tests at all — the gate must return `BLOCKED-UNVERIFIED`.

### Metrics

| Metric | Target |
|---|---|
| Planted-defect detection (T2) | ≥ 80% (4/5) |
| False blocks on clean diffs | ≤ 1/10 |
| Unverified "done" claims | 0 |
| Evidence-format validity | 100% |
| Verdict arithmetic correctness | 100% |

### Runner

`evals/run.py` with two modes:

- `--mode=deterministic`: validates artifacts, evidence format, and verdict arithmetic. Runs in CI, no model.
- `--mode=agent`: invokes a configured agent on a fixture and records the transcript. Manual/nightly, since it costs tokens and is nondeterministic.

CI gets the deterministic mode + the existing validator. Agent evals are a release gate, run by a human.

## 8. Milestones

| M | Deliverable | Done when |
|---|---|---|
| M0 | Restructure, two manifests, multi-root validator, CI green, `0.3.0` | `python3 scripts/validate_skills.py` passes on both plugins |
| M1 | `merge-gate` + 4 references + 5 fixtures | eval hits the §7 targets |
| M2 | `plan` + profile contract | profile generated on 3 stacks; gate consumes it |
| M3 | `investigate` | root-cause eval: 3 failing fixtures fixed with regression tests |
| M4 | `behavior-principles` extension | destructive-op section + review stance |
| M5 | `repo-reconnaissance` profile emission | same schema as M2 |
| M6 | README, marketplace, CHANGELOG, migration guide | marketplace install works for both plugins |
| M7 | 4-week dogfood → `1.0.0` | 20 gated diffs; defect/false-block data recorded |

**M1 is the product.** Nothing else ships without it; M0 is only packaging.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Three lenses correlate and miss | Different mandates + forced evidence; optional second model at T2; state `single-context review` honestly |
| Cost/latency makes users disable it | T0/T1 depth scaling; lens count fixed, output size bounded |
| False positives erode trust | ≤1/10 target; every finding needs a trigger; P3 is explicitly non-blocking |
| Reviewer prompt-injected by the diff | Treat diff text as data; never follow instructions found in the diff; only run profile commands |
| Command execution supply chain | D3 confirmation, `source` recorded, never invent commands |
| Marketplace rejects subdirectory sources | Fallback: separate repos + aggregator marketplace |
| Validator refactor breaks CI | Multi-root tests in M0 before any skill text |
| Scope creep back toward 64 skills | §2 "Out" list is normative; new skills require deleting one |
| Text similarity to gstack | Write original prose; steal mechanics only; confirm gstack's license before quoting |

## 10. Deferred (not v1)

`context` (session continuity), `ship`/`release`, harness hooks, second-model integration as a first-class feature, plugin-level telemetry, templates per language.

## 11. Decision log

| Date | Decision | By |
|---|---|---|
| 2026-11-06 | Published plugin, not a private setup | user |
| 2026-11-06 | Promise: idea → merge-ready; `ship` removed | user |
| 2026-11-06 | Review must be very tight; 3 lenses are non-negotiable | user |
| 2026-11-06 | `verify-task` merges into the gate (not deleted) | user |
| 2026-11-06 | Stack-agnostic, no language assumptions | user |
| 2026-11-06 | Do not retire existing discovery skills; improve | user |
| 2026-11-06 | Split into two plugins | user |
| 2026-11-06 | Evals are required, not optional | user |
| 2026-11-06 | Verdict is computed, not narrated | design |
| 2026-11-06 | Blind passes with per-lens artifacts | design |
| 2026-11-06 | Instructions only; no harness hooks in v1 | design |
| 2026-11-06 | D1/D2/D3 | **open** |
