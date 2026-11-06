# gstack Inventory Summary (committed)

Condensed from the local, gitignored `specs/gstack-skills-inventory.md`
(gstack 1.96.0.0, 2026-11-06). This file exists so a fresh session can
understand what DevLoop replaces without depending on untracked local state.

| Category | Count | Representative skills | Fate in DevLoop v1 |
|---|---|---|---|
| Planning, product, spec | 7 | `office-hours`, `plan-*-review`, `autoplan`, `spec` | `plan` (one skill, no review fan-out) |
| Design and visual | 6 | `design-*`, `diagram` | out of scope |
| Code quality, testing, debugging | 11 | `health`, `verify`, `review`, `qa`, `investigate` | `merge-gate`, `investigate` |
| Documentation | 3 | `document-*`, `make-pdf` | out of scope (existing `code-documenter` stays) |
| Ship, deploy, PR lifecycle | 7 | `ship`, `land-and-deploy`, `canary`, `retro` | out of scope; loop ends at merge-ready |
| Safety, security, permissions | 5 | `careful`, `freeze`, `guard`, `cso` | destructive-op guard only |
| Browser and web automation | 6 | `browse`, `scrape`, `pair-agent` | out of scope |
| iOS on-device | 5 | `ios-qa`, `ios-fix`, `ios-*` | out of scope |
| Agent orchestration and external models | 7 | `codex`, `claude-code`, `captain` | out of scope; second model deferred |
| Context, memory, self-management | 7 | `context-*`, `learn`, `upgrade` | out of scope |

Totals: 64 skills plus the `gstack` router (65 entries), ~6,560 always-on
description tokens.

## What DevLoop keeps

- The **spine** idea: plan → implement → verify → review, ending at merge-ready.
- The **review stance**: attack the diff, require evidence, never trust clean-looking code.
- The **iron law** from `investigate`: no fix before a demonstrated root cause.

## What DevLoop deliberately drops

- Deployment, canaries, retros, browser/iOS automation, agent fleets, and all
  design-production skills.
- The router: 10 skills with sharp descriptions replace 65 routed entries.
- Review fan-out (CEO/eng/design/DX): one gate with three disjoint lenses.
