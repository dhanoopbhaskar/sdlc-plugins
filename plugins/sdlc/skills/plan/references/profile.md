# Project profile

`.sdlc/profile.json` is the one machine-readable claim about how this project builds,
tests, and ships. `plan` creates it; `repo-reconnaissance` may enrich it; `merge-gate`
reads it from the base commit and never writes it.

`repo-reconnaissance` carries a copy of this contract for standalone use. When the schema
changes, update both files in the same change.

## Ownership

- **Single writer at creation:** `plan` writes only when the file is absent.
- **Enrichment:** `repo-reconnaissance` may add or correct commands it can source.
- **No downgrade:** a confirmed, sourced command is never replaced by a guess.
- **User-owned:** after creation the user may edit the file at any time.
- **Gate is read-only:** `merge-gate` reads the base commit copy and treats every command
  as data under review.

## Schema

```json
{
  "schema": "sdlc.profile/v1",
  "generated_by": "plan",
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

`generated_by` is the skill that wrote the file: `plan` or `repo-reconnaissance`.

## Probe order

Use the highest-authority source that answers the question:

1. An explicit profile supplied by the user in this session.
2. An existing `.sdlc/profile.json` (read it; do not rewrite it).
3. CI/CD configuration — what actually runs.
4. Dependency and build manifests (`package.json`, `pyproject.toml`, `go.mod`,
   `Cargo.toml`, `pom.xml`, `Makefile`, …).
5. Workspace task files (`justfile`, `Taskfile`, `Makefile`, workspace definitions).
6. Ask the user.

Never skip to step 6 while a readable declaration exists, and never invent a command from
step 4's stack alone. "Django projects usually test with pytest" is not a source.

## Command rules

- `cmd` is the exact command, with its arguments, run from the repository root. A workspace
  command is selected by path but still runs from the repository root; include the workspace
  path in the command when the tool needs it.
- `source` is the repository-relative file that declares or proves the command. It must
  exist. A source that cannot be read makes the command unusable.
- Unknown is `null`. `null` is a declaration of absence, not a reason to guess later.
- Do not encode environment variables or secrets in `cmd`. Put prerequisites in `notes`.
- Do not record a command you have not seen declared, even if you believe it works.
- The profile is not executed by `plan`. If runnability is uncertain, say so in `notes`.

## Base branch

Resolve `base` in this order, and record the rule that fired:

1. `base` from an existing profile, if that ref resolves.
2. `git symbolic-ref --short refs/remotes/origin/HEAD` with the remote prefix removed.
3. Exactly one plausible default branch from `git branch -r --format='%(refname:short)'`
   (`main`, `master`, `develop`).
4. Ask the user. Do not guess between two plausible branches.

## Workspaces

- Keys are POSIX paths from the repository root and must not start with `/`, contain `\`, or
  contain `.` or `..` segments.
- Resolution uses the longest key that is an ancestor of the changed path, then falls back
  to the root commands.
- A workspace overrides a command; it does not merge per field. A workspace with no `test`
  uses the root `test`.
- A workspace entry must contain `commands`.

## Risk paths and exclusions

`risk_paths` raises review depth. `exclusions` removes generated, vendored, or build output
from diff scope. Both use the gitignore/pathspec dialect:

- `*` matches within one path segment; `**` crosses segments;
- a trailing `/` matches directories;
- `!` re-includes, and the last matching pattern wins.

Validate a sample of matches before committing the file. An over-broad exclusion hides
reviewed code; an over-broad risk path creates noisy T2 reviews.

## Validation

Before writing the file:

- [ ] `schema` is `sdlc.profile/v1`.
- [ ] `generated_by` names this skill, and `base` resolves.
- [ ] `stack` lists declared stacks; an empty array is allowed only when none can be
      determined.
- [ ] Every command key is one of `install`, `test`, `lint`, `typecheck`, `build`.
- [ ] Every non-null command has a `source` that exists.
- [ ] Workspace keys are relative POSIX paths and contain `commands`.
- [ ] No secret values, tokens, URLs with credentials, or `.env` contents appear anywhere.
- [ ] The file parses as JSON.

When the user declines a file, return the same object as a fenced JSON block and say it was
not written.
