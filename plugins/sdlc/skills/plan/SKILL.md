---
name: plan
description: "Plans a change before code: falsifiable acceptance criteria, risk register, review tier, and a project profile. Use to spec or break down work."
---

# Plan

Turn a request into a spec that a reviewer can grade. This skill does not implement,
estimate delivery dates, or approve its own output.

## Non-negotiables

1. No normal plan ships without at least one falsifiable acceptance criterion.
2. Never invent scope. Ask a question, or switch to spike mode on purpose.
3. An unknown stays an unknown: `null`, an open question, or a recorded assumption. Never a
   silent guess.
4. The plan proposes a tier; `merge-gate` re-derives it. If they disagree, the higher wins.
5. Write `.sdlc/profile.json` only when it is absent, or with explicit approval for a proposed
   edit.
6. Stop at approval. Planning ends before the first implementation edit.

## Modes

| Mode | When | Output |
|---|---|---|
| **Normal** | The request can be expressed as testable criteria. | Spec with ACs, risks, tier, profile. |
| **Spike** | The question is "is this possible or which approach works", or scope cannot become ACs after three clarifications. | A question, a timebox, and exit criteria — never ACs. |

Spike mode must be explicit. Label the artifact `SPIKE` and say what evidence ends the spike.
A spike result is input to a later normal plan; it is never presented as merge-ready.

## Procedure

### 1. Clarify

Ask at most **three** questions, and only questions that change scope or an acceptance
criterion. Record each question and answer verbatim.

Do not ask what the repository already answers. Read the code, manifests, CI, and existing
specs first. If more than three questions remain, the request is not ready: narrow the scope
or switch to spike mode.

### 2. Probe the project

Build the project profile, or read the existing one before writing criteria. A profile supplied
by the user in this session wins first. Otherwise read the existing profile, then CI, then
manifests, then workspace task files, then ask. The full contract, probe order, and schema are
in [references/profile.md](references/profile.md).

Record commands with the file that declares them. A command with no source is `null`. Never
invent a command because the stack usually has one.

### 3. Write the spec

Use [references/spec-template.md](references/spec-template.md). Keep these sections, and mark
any section that does not apply as `none` rather than deleting it:

- problem and goal;
- non-goals;
- assumptions and constraints;
- open questions;
- acceptance criteria;
- risks;
- risk paths and proposed tier;
- profile state.

State the user-visible outcome before any implementation detail.

### 4. Acceptance criteria

Each AC is one observable outcome and one check. Write them as `AC-1`, `AC-2`, in priority
order.

An AC is falsifiable when a command or a named manual check can return pass or fail without
interpretation.

| Bad | Why | Better |
|---|---|---|
| Login should work | No observable outcome. | An expired session cookie returns `401` and does not refresh the token. |
| Add caching | Names a technique, not behavior. | A repeated request for the same tenant key returns the cached value; a different tenant misses. |
| Improve error handling | No trigger or result. | A failed database write returns `503` and logs the request id once. |

Rules:

- One behavior per AC, including the negative case for user-facing changes.
- Each AC names its check: a test id, a command, or a manual procedure.
- If a requirement cannot be graded, it is a non-goal or an open question, not an AC.
- Do not restate the implementation as the criterion.

### 5. Risk register

Record the risks that would make the change fail in production: what can happen, how likely,
how bad, how it is detected, and how it is mitigated or accepted. Cover behavior, data,
security, operations, and rollback. A risk that cannot be mitigated becomes an open question,
not a silent omission.

### 6. Risk paths and tier

Propose the paths whose change should raise review depth, using the gitignore/pathspec glob
dialect (`*` within a segment, `**` across segments, trailing `/` for directories). Then
propose a tier:

| Tier | Proposal trigger |
|---|---|
| T0 | Docs, comments, copy, formatting only. |
| T1 | Any logic, test, or non-risky config change. |
| T2 | Auth, payments, deletion, migrations, infrastructure, crypto, external IO, concurrency, CI/IaC, or `.sdlc/profile.json`. |

Write the rationale. `merge-gate` will derive the final tier from the diff and the base
profile, so an optimistic proposal does not lower review depth.

### 7. Bootstrap the profile

If `.sdlc/profile.json` is absent, write it from the probe. If it exists, read it and never
overwrite it; record drift between the profile and the repository as an open question. When
the user asks for a change, show the proposed diff and apply it only with explicit approval.

The profile is a claim about the project, not a convenience file. Every command must have a
`source` that exists. Unknown commands are `null`. Never copy secret values into the profile.
The file is user-owned after creation and is edited deliberately, not regenerated behind the
user's back.

### 8. Present for approval

Return the spec path (or the issue text), the ACs, the proposed tier, and any open questions.
Ask for approval before implementation starts. Do not mark the plan approved yourself.

## Output contract

| Artifact | Default path | Notes |
|---|---|---|
| Spec | `specs/<slug>.md` | Follow an existing repository convention when one exists. |
| Issue text | conversation | Produce the same sections as Markdown; do not create a file unless asked. |
| Profile | `.sdlc/profile.json` | Write only when absent, or with approval for a proposed edit. Return the JSON when the user declines a file. |

## Completion gate

In normal mode, do not report the plan complete until all are true:

- [ ] At most three clarifying questions were asked, each with its answer recorded.
- [ ] The spec uses the required sections; non-goals are explicit.
- [ ] At least one AC exists, each has an observable outcome and a named check, and each can
      return pass or fail without interpretation.
- [ ] Assumptions, open questions, and ungradable requirements are recorded rather than
      hidden.
- [ ] The risk register covers behavior, data, security, operations, and rollback.
- [ ] `risk_paths` use the documented glob dialect and the tier has a rationale.
- [ ] The profile is valid and sourced, contains no secrets, and was written only if absent or
      edited with explicit approval.
- [ ] The plan states that it awaits human approval.

In spike mode, the gate is: one question, a timebox, exit criteria, the evidence to capture,
and a decision rule. A spike has no ACs and no approval section.

## Failure modes

| Situation | Action |
|---|---|
| Scope ambiguity blocks ACs | Ask; if still blocked after three questions, switch to spike mode or stop. |
| Stack or commands cannot be determined | Ask. Record `stack: []` and `null` commands; do not guess. |
| Existing profile conflicts with the repository | Keep the profile, record the drift, and ask which is authoritative. |
| A requirement has no observable outcome | Demote it to a non-goal or an open question. |
| User asks for implementation | Hand off with the approved spec; this skill stops. |
| User asks for a plan without ACs | Offer spike mode explicitly; do not ship a normal plan. |

## Do not

- Do not generate production code, scaffolding, or implementation patches in normal mode. A
  spike may produce a labelled prototype as evidence, never as an approved change.
- Do not invent commands, versions, paths, or acceptance criteria.
- Do not write a normal plan whose ACs cannot fail.
- Do not overwrite an existing profile or edit one without approval.
- Do not claim the plan is approved or merge-ready.
- Do not turn a spike into a delivery commitment.
