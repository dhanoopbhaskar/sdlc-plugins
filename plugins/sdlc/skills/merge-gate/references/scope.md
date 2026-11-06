# Phase 1 — Scope

Establish exactly what is under review before any fact is proven or any lens opens. If scope is wrong, every later phase is wasted work.

## Resolve the base

Try in order, and record which rule fired:

1. `base` in the base-commit `.sdlc/profile.json`, if that ref resolves.
2. `git symbolic-ref --short refs/remotes/origin/HEAD` with the remote prefix removed.
3. `git branch -r --format='%(refname:short)'` when it names exactly one likely default (`main`, `master`, `develop`).
4. Ask the user. Do not guess between two plausible branches.

Then compute the merge base. Never diff against a branch tip.

```bash
git fetch --no-tags origin <base>     # only with approval; skip if offline
BASE_SHA=$(git merge-base HEAD <base>)
git diff --name-status "$BASE_SHA"..HEAD
git diff --stat "$BASE_SHA"..HEAD
git diff "$BASE_SHA"..HEAD
```

`git fetch` is a network operation. Ask first. If the remote is unreachable, use the local ref and record `base_stale: true` in `scope.md`.

## Dirty section

The working tree is reviewed separately, never merged into the committed diff:

```bash
git status --porcelain=v1
git diff --stat
git diff
git ls-files --others --exclude-standard
```

Untracked files are listed by path. Read them only if they are text and in scope; otherwise mark them `unread`.

## Diff hash

Hash the exact bytes reviewed:

- committed: `git diff "$BASE_SHA"..HEAD`
- dirty: `git diff` plus the concatenated untracked file contents, in path order

Write it as `sha256:<hex>`. The same value goes in `verdict.md`. For a fixture, hash `diff.patch`.

## Classify every changed path

| Bucket | Rule |
|---|---|
| `reviewed` | text, in scope, read in full |
| `dirty` | uncommitted change, reviewed in its own section |
| `excluded` | matches base-profile `exclusions`; list it and the matching pattern |
| `binary` | name, size, and type; content not reviewed |
| `unread` | could not be read; becomes `UNPROVEN` |

Never silently drop an excluded path. `scope.md` shows it with the pattern that excluded it.

## Chunking

A diff over roughly 400 changed lines is chunked by file, then by hunk. Read every chunk or mark it `unread`. A chunk that is not read is not reviewed, and the verdict says so.

## Acceptance criteria

- Quote each AC verbatim and record its source (`plan` path, issue, or user message).
- If no AC exists, reconstructing one does not make it real: mark `acs: "unconfirmed"`, which forces `UNSCOPED`.
- If an AC is not falsifiable, say which part cannot be graded and why.

## Tier

Re-derive the tier from the diff **and the base profile**. `plan` only proposes.

| Tier | Trigger |
|---|---|
| T0 | docs, comments, copy, formatting only |
| T1 | any logic, test, or non-risky config change |
| T2 | matches base-profile `risk_paths`, or touches auth, payments, deletion, migrations, infrastructure, crypto, external IO, concurrency, CI/IaC, or `.sdlc/profile.json` |
| T3 | `plan` proposed exhaustive analysis, or the change is cross-module or changes a public API, schema, event, CLI, or data contract |

If `plan` proposed a higher tier, keep the higher one. A diff cannot lower its own tier: the profile used for tiering comes from the base commit.

T3 is a plan-side analysis depth. Re-derive it from the same triggers, run the review at least
as strictly as T2, and record it. The gate does not grade the plan's impact map; an
undispositioned impact entry is a review note, not a verdict rule. Throughout the gate,
`T2-relevant` means the risk class and applies to T3 as well.

## `scope.md` template

```markdown
# Scope — <slug>

- base: <ref>
- base_sha: <sha>
- head_sha: <sha>
- base_stale: false
- diff_hash: sha256:<hex>
- tier: T1
- acs: confirmed
- isolation: isolated

## Acceptance criteria

1. "<verbatim AC>" — source: specs/<file>.md

## Changed files

| Path | Bucket | Lines | Note |
|---|---|---|---|
| src/app.py | reviewed | +12 −3 | |
| docs/x.md | excluded | +4 −0 | matches exclusions: docs/** |
| assets/logo.png | binary | — | 12 KB PNG |

## Dirty section

| Path | State | Bucket |
|---|---|---|
| src/app.py | modified | dirty |

## Chunks

| Chunk | Files | Read |
|---|---|---|
| 1 | src/app.py | yes |
| 2 | src/db.sql | no — unread |

## Tier rationale

- matched risk_paths: `src/auth/**`
- proposed by plan: T1; gate: T2; higher wins.
```
