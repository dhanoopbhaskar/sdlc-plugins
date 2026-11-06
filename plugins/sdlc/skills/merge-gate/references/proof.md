# Phase 2 — Proof

Facts only. No findings, no severity, no recommendations. A lens may challenge a fact later; it may not invent one.

## The five facts

1. **Requirement** — the AC this change implements, quoted. Not a paraphrase.
2. **Test** — the commands that ran, with receipts. A failure is never summarized as a pass.
3. **Regression** — the behavior at risk and the check that covers it. "The suite passes" is not regression evidence.
4. **Diff justification** — one line per changed file explaining why it exists. Any line that cannot be traced to the AC is recorded as out-of-scope and carried into L1; it is not accepted because tests pass.
5. **Unproven** — what could not be checked, and the exact reason.

## Command receipts

Before running a command, print:

```
command:  <exact command>
cwd:      <absolute path>
source:   <profile source file> @ <base_sha>
approval: sha256:<hash of cmd + cwd + env allowlist>
```

After running, record:

```
exit:           0
duration:       12.4s
output_sha256:  sha256:<hash of combined stdout/stderr>
tail:
  <last 20 lines, secrets redacted>
```

Rules:

- One receipt per command. Do not merge two runs into one line.
- A timeout is an exit state, not a pass. Record it.
- A command that cannot start is `BLOCKED-ENV` and names the prerequisite.
- An empty test selection (zero tests collected) is not a pass. Record the count.
- Never paste a full log with credentials. Redact and hash the original.

## Which commands

Use the base-commit profile for the touched workspaces. Run `test` always; run `lint`, `typecheck`, and `build` when the change can affect them.

- A `null` command means "not declared". Do not invent one.
- If a declared command is stale or wrong, do not silently substitute. Run a command the user types in this session and record it as `user-supplied`, or record the gap as `UNPROVEN`.
- If the profile has no test command and the AC requires behavior, the verdict cannot be `MERGE-READY` without user-supplied evidence.
- Commands that need the network or credentials are `BLOCKED-ENV` when unavailable. Do not work around them silently.

## Regression evidence

Name the behavior, then the check:

- A bug fix needs a test that fails on the base and passes on the change, or an equivalent demonstrated reproduction.
- A refactor needs the covering tests plus the behavioral invariant they protect.
- A docs-only change can state "no runtime behavior; link check only" and cite the check.
- "No regression test exists" is a fact. Write it down; do not soften it.

## `proof.md` template

```markdown
# Proof — <slug>

## 1. Requirement

AC 1: "<verbatim>" — source: <path>

## 2. Commands

### test

```
command:        uv run pytest -q
cwd:            /repo
source:         pyproject.toml @ <base_sha>
approval:       sha256:<hex>
exit:           0
duration:       12.4s
output_sha256:  sha256:<hex>
tail:
  41 passed in 12.31s
```

## 3. Regression

- Behavior at risk: expired sessions are rejected.
- Covering check: `tests/test_session.py::test_expired_cookie` (ran above).
- Limits: no test covers clock skew.

## 4. Diff justification

| File | Why it exists | In scope |
|---|---|---|
| src/auth/session.py | compare `exp` before refresh | yes |
| src/util.py | formatting only | no — carried to L1 |

## 5. Unproven

| Item | Reason | Blocks |
|---|---|---|
| prod-cardinality load test | no capacity environment | yes |
| mobile client compatibility | client not in this repo | yes |
```
