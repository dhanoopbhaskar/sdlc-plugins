---
name: sdlc-behavior-principles
description: "Behavioral guardrails for SDLC planning, implementation, and review. Use when shaping plans, implementing approved scope, or reviewing changes to surface assumptions, keep solutions simple, enforce surgical diffs, and require verifiable checks."
---

# SDLC Behavior Principles

Use these guardrails with repository conventions and stage prompts.

## 1. Think Before Coding

- Do not guess when requirements are ambiguous.
- State assumptions and ask targeted clarifying questions.
- If blocked, stop and request minimum missing input.

## 2. Simplicity First

- Make the smallest change that satisfies approved scope and ACs.
- Avoid speculative abstractions or optionality not requested.
- Prefer local explicit logic over premature generalization.
- If a simpler design achieves the same outcome with lower risk, choose it.

## 3. Surgical Changes

- Every change must trace to approved plan scope, rework feedback, or required tests.
- No drive-by refactors, style rewrites, or unrelated cleanup.
- Match local conventions in touched files.
- Remove only unused artifacts introduced by your own changes; leave unrelated legacy cleanup for separate work.

## 4. Goal-Driven Execution

- Break work into verifiable units with explicit checks.
- If checks fail, iterate or report a concrete blocker with evidence.
- Prefer incremental steps over all-at-once changes.

## Stage Focus

- Planning: capture assumptions and unresolved questions before final scope.
- Implementation: start each unit with its intended outcome and verification target; keep edits aligned to approved plan items.
- Review: verify acceptance-criteria coverage and flag out-of-scope changes; classify their severity.

## Quick Self-Check

- Did I ask before guessing?
- Is this the simplest plan-compliant solution?
- Can I justify every changed line against approved scope?
- Do I have objective checks proving the change works?
