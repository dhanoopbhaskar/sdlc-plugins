# Spec template

Copy this template into `specs/<slug>.md`, or return the same sections as issue text. Keep
`none` where a section does not apply so a reviewer can tell "absent" from "forgotten".

```markdown
# <Title>

- status: DRAFT | AWAITING-APPROVAL | APPROVED | SPIKE
- date: <YYYY-MM-DD>
- tier: T0 | T1 | T2 | T3 (exhaustive)
- profile: created | existing | not-written

## Problem

What is wrong today, for whom, and what happens if nothing changes. No solution language.

## Goal

The user-visible outcome after this change, in one or two sentences.

## Non-goals

What this change deliberately does not do. Name the tempting adjacent work.

## Assumptions

Beliefs that are load-bearing and not yet proven. Each one names how it will be checked.

## Constraints

Compatibility, deadlines, contracts, or environments that limit the design.

## Open questions

| # | Question | Blocks | Owner |
|---|---|---|---|
| Q1 | <question> | <AC or section> | <person> |

## Acceptance criteria

| ID | Criterion (falsifiable) | Check |
|---|---|---|
| AC-1 | <observable outcome> | <test id, command, or manual procedure> |
| AC-2 | <negative or edge case> | <check> |

## Impact map (T3)

Every file that can change, plus every file that can be affected without changing. Mark a
section `none` when the tier is not T3.

| Path | Relationship | Disposition | Evidence |
|---|---|---|---|
| `src/session.ts` | direct edit | change | AC-1 |
| `src/api/handler.ts` | calls the changed function | no-change | call site L42; signature unchanged |
| `clients/web/session.ts` | consumes the response contract | unproven | contract test not written |

Disposition is exactly one of `change`, `no-change`, `unproven`. `change` paths appear in the
changed set; `unproven` paths become open questions with an owner.

## Approach decision (T3)

- **chosen:** <the approach>
- **why it works:** <the mechanism that satisfies the ACs>
- **rejected:** <alternative> — <why it fails>
- **invalidated by:** <evidence that would reopen the decision>

A T3 plan with no rejected alternative must state why no other approach was viable.

## Blast radius (T3)

| If this is wrong | Breaks | Detected by | Rollback |
|---|---|---|---|
| <failure> | <user or system impact> | <signal or check> | <revert path, data safety> |

## Risks

| Risk | Likelihood | Impact | Detection | Mitigation / acceptance |
|---|---|---|---|---|
| <what can fail> | low/med/high | low/med/high | <signal> | <action> |

## Risk paths

- `src/auth/**` — authentication and session handling.
- `migrations/**` — schema changes are not reversible without a down path.

## Tier rationale

- proposed: T2
- why: matches `risk_paths`; changes authorization before a response.

## Profile

- path: `.sdlc/profile.json`
- state: created | existing | not-written
- notes: <prerequisites, unresolved commands>

## Approval

Awaiting human approval. Implementation must not start before the status is `APPROVED`.
```

## Writing acceptance criteria

An AC is a claim that can be **falsified by a check**. Prefer the smallest observable
outcome. If two behaviors need two checks, write two ACs.

- **Good:** "A request with an expired cookie and a refreshed token receives `401`, and the
  response does not set a new session cookie." — can be a test.
- **Good:** "Running `make docs` on a clean checkout produces no broken internal links." —
  can be a command.
- **Bad:** "Sessions are secure." — no trigger, no result.
- **Bad:** "Refactor the session module." — an implementation instruction.

For behavior changes, include at least one AC for the failure or edge path, not just the
happy path. For documentation-only work, the check can be a link check or a named review
step.

## Spike template

Use this instead of the normal template when the work is a question, not a delivery:

```markdown
# SPIKE — <question>

- status: SPIKE
- timebox: <hours or days>
- exit criteria: <evidence that ends the spike>

## Question

The single decision this spike informs.

## Why it cannot be planned yet

What is unknown, and why the unknowns prevent falsifiable ACs.

## Approach

The smallest experiment that produces the missing evidence.

## Evidence to capture

Commands, measurements, prototypes, or sources that will be recorded.

## Decision rule

What result supports which follow-up plan. A spike that ends without a decision is incomplete.
```

A spike may produce a prototype, but the prototype is evidence, not an approved change. Any
production change needs a normal plan with ACs afterwards.

## Risk register prompts

Cover each category; write `none` when a category genuinely does not apply.

- **Behavior:** wrong output, missed edge case, changed contract.
- **Data:** loss, partial write, migration lock, retention breach.
- **Security:** authz bypass, injection, secret exposure, untrusted input.
- **Operations:** new env var, deploy ordering, missing alert, rollback cost.
- **Compatibility:** API, schema, event, client, or consumer breakage.
- **Rollback:** can the change be reverted without losing data?

For T3, the impact map supplies the file-level surface and the blast radius supplies the
failure modes. The risk register must still name likelihood, impact, detection, and mitigation
for each one.

## Tier prompts

- **T0** only when every changed line is non-executable: docs, comments, copy.
- **T1** for ordinary logic, tests, or non-risky config.
- **T2** when the change touches auth, payments, deletion, migrations, infrastructure,
  crypto, external IO, concurrency, CI/IaC, or the profile itself.
- **T3 (exhaustive)** when the user asks for it, or the change is cross-module, changes a
  public API, schema, event, CLI, or data contract, is an architectural refactor, or the
  approach itself is in question. T3 requires the impact map, approach decision, and blast
  radius above.

When unsure between two tiers, propose the higher one and say why. `merge-gate` re-derives
the tier and keeps the higher of the two. T3 analysis is owned by `plan`; the gate does not
grade the impact map.
