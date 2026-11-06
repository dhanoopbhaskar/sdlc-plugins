# Project profile emission

`plan` defines the profile contract. Reconnaissance emits or enriches the same file so the
review gate can run the project without being taught a stack.

This file mirrors the canonical contract in the `plan` skill for standalone use. When the
schema changes, update both files in the same change.

Path: `.sdlc/profile.json`. Committed by default. Schema: `sdlc.profile/v1`.

## Schema

```json
{
  "schema": "sdlc.profile/v1",
  "generated_by": "repo-reconnaissance",
  "base": "main",
  "stack": ["python"],
  "commands": {
    "install":   { "cmd": "uv sync", "source": "uv.lock" },
    "test":      { "cmd": "uv run pytest -q", "source": "pyproject.toml" },
    "lint":      { "cmd": "uv run ruff check .", "source": "pyproject.toml" },
    "typecheck": { "cmd": "uv run mypy .", "source": "pyproject.toml" },
    "build":     null
  },
  "workspaces": {
    "services/api": {
      "commands": {
        "test": { "cmd": "uv run pytest services/api -q", "source": "services/api/pyproject.toml" }
      }
    }
  },
  "ci": { "file": ".github/workflows/ci.yml", "jobs": ["test", "lint"] },
  "risk_paths": ["src/auth/**", "src/payments/**", "migrations/**"],
  "exclusions": ["**/generated/**", "vendor/**"],
  "notes": "Tests require DATABASE_URL; use docker compose up -d db"
}
```

Required: `schema`, `generated_by`, `base`, `stack`, `commands`. Optional: `workspaces`,
`ci`, `risk_paths`, `exclusions`, `notes`.

## Probe order

Use the first source that answers the question:

1. An explicit profile supplied by the user in this session.
2. An existing `.sdlc/profile.json`.
3. CI/CD configuration — what actually runs.
4. Dependency and build manifests.
5. Workspace task files (`justfile`, `Taskfile`, workspace scripts).
6. Ask.

Reconnaissance has already read these in steps 3–5. Do not invent a command from a stack name:
"this is a Django repo" is not evidence that `pytest` is the test command.

## Command rules

- `cmd` is exact and runs from the repository root. A workspace command is selected by path but
  still runs from the repository root; include the workspace path in the command when the tool
  needs it.
- `source` is the repository-relative declaration file and must exist at the survey commit.
- Unknown is `null`. `null` is a fact the gate can report, not a prompt to guess.
- Record prerequisites (services, env var names, fixtures) in `notes`, never values.
- Do not execute a discovered command to verify it during reconnaissance. Record that it is
  declared, not that it passed.
- If two sources disagree, trust the higher-authority one (CI, then lockfile/runtime pin, then
  manifest, then README) and record the discrepancy as an open question.

## Base branch

Resolve `base` in this order:

1. `base` from an existing profile that resolves.
2. `git symbolic-ref --short refs/remotes/origin/HEAD` with the remote prefix removed.
3. Exactly one plausible default branch from `git branch -r` (`main`, `master`, `develop`).
4. Ask. Do not guess.

## Workspaces

- Keys are relative POSIX paths from the repository root; no leading `/`, no `\`, no `.` or
  `..` segments.
- Resolve the longest key that is an ancestor of a changed path, then fall back to the root
  commands.
- A workspace overrides a command; it does not inherit per field. A workspace with no `test`
  uses the root `test`.
- Every workspace entry contains `commands`.

## Risk paths and exclusions

- `risk_paths` raises review depth. Include the paths where a defect would be expensive:
  auth, payments, deletion, migrations, infrastructure, crypto, external IO, concurrency.
- `exclusions` removes generated, vendored, and build-output paths from diff scope. Every
  pattern must have evidence from step 8; a silent exclusion hides reviewed code.
- Both use the gitignore/pathspec dialect: `*` within a segment, `**` across segments, a
  trailing `/` for directories, `!` to re-include (last match wins).

## Enrichment rules

When a profile already exists:

- Preserve it. Do not regenerate it from scratch.
- Add a command only when the new source is stronger than the existing one, or when the
  existing value is `null`.
- Never replace a sourced command with an unsourced guess.
- Never downgrade `generated_by`, and never overwrite a profile generated after the current
  survey commit.
- If the existing profile conflicts with the repository, keep it and record the drift as an
  open question. The user decides which is authoritative.
- Update `generated_by` to `repo-reconnaissance` only when this survey actually changes the
  file, and say what changed in the bundle log.

## Validation

Before writing:

- [ ] `schema` is `sdlc.profile/v1`.
- [ ] `generated_by` is `repo-reconnaissance`, and `base` resolves.
- [ ] `stack` lists declared stacks (empty is allowed when the stack is undetermined).
- [ ] Every command key is one of `install`, `test`, `lint`, `typecheck`, `build`.
- [ ] Every non-null command has an existing `source`.
- [ ] Workspace keys are relative POSIX paths and contain `commands`.
- [ ] `risk_paths` and `exclusions` match real paths and have evidence.
- [ ] No secret values, credential-bearing URLs, or `.env` contents appear.
- [ ] The file parses as JSON.

If the user declines a written file, return the same object as a fenced JSON block and note
that it was not written.
