# Portable Read-Only Commands

These recipes assume a POSIX shell and `git`. Every command is read-only. `rg`, `cloc`, and
`tokei` are optional; when one is missing, use the fallback rather than installing it. On a
non-POSIX host, use the equivalent and record what you used.

Set the repository root once:

```sh
repo="<path-to-repo>"
```

The `rg` recipes below are optional. When `rg` is unavailable, use the `grep -RIlE` fallback
shown under [Find data and messaging surfaces](#find-data-and-messaging-surfaces), substituting
the pattern; do not install `rg` just to run a search.

## Pin the snapshot

```sh
git -C "$repo" rev-parse HEAD
git -C "$repo" rev-parse --abbrev-ref HEAD
git -C "$repo" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##'
git -C "$repo" status --porcelain
git -C "$repo" remote -v
git -C "$repo" submodule status
```

Record the SHA, default branch, checked-out branch (if different), dirty state, remote, and
submodules in the ledger `# Repositories` row (and in the registry entry for a multi-repo
estate). A dirty tree means the analysis may not match any commit.

## Census

`git ls-files` lists tracked files and is usually the best first-party file list. It does not
include untracked files. Decide the denominator once, define `lsf`, and use it for every
file-list recipe in this document. Choose one definition:

```sh
# Tracked files only (default).
lsf() { git -C "$repo" ls-files; }

# Or, when untracked code is in scope:
lsf() { git -C "$repo" ls-files --cached --others --exclude-standard; }
```

Count untracked files separately so the choice is visible:

```sh
git -C "$repo" ls-files --others --exclude-standard | wc -l
lsf | wc -l
lsf | awk -F/ 'NF>1 {print $1}' | sort | uniq -c | sort -rn | head -40
```

Record which definition you used; it is the denominator for coverage.

Fallback when the directory is not a git repository:

```sh
find "$repo" -type f -not -path "*/.git/*" | wc -l
```

Files by extension (extensionless files and dotfiles are reported as `(none)`):

```sh
lsf | awk -F/ '{print $NF}' \
  | awk -F. 'NF>1 && $1!="" && $NF!="" {print $NF; next} {print "(none)"}' \
  | sort | uniq -c | sort -rn | head -30
```

Churn per top-level directory (last 12 months):

```sh
git -C "$repo" log --since="12 months ago" --name-only --pretty=format: \
  | awk -F/ 'NF>1 {print $1}' | sort | uniq -c | sort -rn | head -30
```

Largest directories by file count (root-level files count as `.`):

```sh
lsf \
  | awk -F/ 'NF>1 {d=$0; sub("/[^/]*$","",d); print d} NF==1 {print "."}' \
  | sort | uniq -c | sort -rn | head -30
```

Line counts are optional and often misleading as a progress metric. If `cloc` or `tokei` is
installed, record the tool and version; otherwise use `wc -l` on the first-party list.

## Find manifests and build files

```sh
lsf \
  | grep -Ei '(^|/)(package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.ya?ml|.*\.(cs|fs|vb)proj|.*\.sln|global\.json|packages\.lock\.json|Directory\.Build\.props|pom\.xml|build\.gradle(\.kts)?|settings\.gradle(\.kts)?|build\.sbt|go\.mod|go\.sum|Cargo\.toml|Cargo\.lock|rust-toolchain[^/]*|pyproject\.toml|requirements[^/]*\.txt|setup\.py|Pipfile|poetry\.lock|uv\.lock|Gemfile|Gemfile\.lock|.*\.gemspec|composer\.json|composer\.lock|mix\.exs|mix\.lock|rebar\.config|CMakeLists\.txt|meson\.build|conanfile\.(txt|py)|vcpkg\.json|Package\.swift|Podfile|Cartfile|pubspec\.yaml|pubspec\.lock|deps\.edn|project\.clj|.*\.cabal|stack\.yaml|DESCRIPTION|renv\.lock|cpanfile|dbt_project\.ya?ml|Makefile\.PL|AndroidManifest\.xml|project\.pbxproj|contents\.xcworkspacedata|Makefile|Dockerfile|Containerfile|.*\.tf|.*\.bicep|Pulumi\.ya?ml|template\.ya?ml)$'
```

Narrow or extend the pattern for the estate; the goal is a candidate list to read, not a
complete taxonomy.

## Find workspace roots (monorepo)

```sh
lsf \
  | grep -Ei '(^|/)(pnpm-workspace\.ya?ml|nx\.json|turbo\.json|lerna\.json|rush\.json|go\.work|settings\.gradle(\.kts)?|Directory\.Build\.props|.*\.sln)$'
```

Read each hit. A workspace declaration is stronger evidence than a `packages/` directory.

## Find CI and release definitions

```sh
lsf | grep -E '(^|/)\.(github/workflows|gitlab-ci|circleci|buildkite|azure-pipelines|tekton)/|(^|/)(Jenkinsfile|\.gitlab-ci\.ya?ml|azure-pipelines\.ya?ml|bitbucket-pipelines\.ya?ml)$'
```

## Find deployment surface

```sh
lsf \
  | grep -Ei '(^|/)(Dockerfile|Containerfile|docker-compose[^/]*\.ya?ml|Chart\.yaml|kustomization\.ya?ml|Procfile|serverless\.ya?ml|template\.ya?ml|.*\.tf|.*\.bicep|Pulumi\.ya?ml|app\.ya?ml)$'
```

## Find data and messaging surfaces

```sh
lsf \
  | grep -Ei '(^|/)(migrations?|db|database|schema|sql|orm|entities|models|repositories)/|\.(sql|proto|avsc|graphql)$'
```

For messaging, search declarations rather than paths:

```sh
rg -l --hidden -g '!**/.git/**' -g '!.env*' -g '!**/*.env' \
  -g '!**/{secrets,credentials}/**' -g '!**/*.{pem,key,p12,jks,pfx}' \
  -g '!**/{id_rsa,id_ed25519,.npmrc,.netrc,.pgpass}' -g '!**/*.tfstate*' \
  -e 'topic|queue|subscription|consumer|producer|dead[-_ ]?letter|exchange' "$repo" | head -100
```

`rg -l` lists candidate files only; matching values are never printed. Open a file only after
confirming it is not a secret store.

Fallback without `rg`:

```sh
grep -RIlE 'topic|queue|subscription|consumer|producer|dead[-_ ]?letter|exchange' "$repo" \
  --exclude-dir=.git --exclude='.env*' --exclude-dir=secrets --exclude-dir=credentials \
  --exclude='*.pem' --exclude='*.key' --exclude='*.p12' --exclude='*.tfstate*' \
  --exclude='.npmrc' --exclude='.netrc' --exclude='.pgpass' \
  | head -100
```

## Find configuration and secret keys (never values)

```sh
lsf \
  | grep -Ei '(^|/)(\.env[^/]*|.*\.(env|ini|conf|config|properties|ya?ml|toml|json))$'
```

Read only key names. Do not paste values into the bundle or the conversation. If a file is
clearly a secret store, record its path and skip the contents.

## Find generated and vendored code

```sh
rg -l --hidden -g '!**/.git/**' -g '!.env*' -g '!**/*.env' \
  -g '!**/{secrets,credentials}/**' -g '!**/*.{pem,key,p12,jks,pfx}' \
  -g '!**/{id_rsa,id_ed25519,.npmrc,.netrc,.pgpass}' -g '!**/*.tfstate*' \
  -e 'Code generated .* DO NOT EDIT|auto-?generated|do not edit' "$repo" | head -50
lsf | grep -Ei '(^|/)(vendor|third[_-]?party|node_modules|dist|build|target|bin|obj|generated|gen)/' | head -50
```

A listed file is a candidate, not a conclusion. Confirm with the generator config or build output
before opening it, and skip files that are secret stores.

## Find entry points

Search for the project's own routing and process declarations:

```sh
rg -l --hidden -g '!**/.git/**' -g '!.env*' -g '!**/*.env' \
  -g '!**/{secrets,credentials}/**' -g '!**/*.{pem,key,p12,jks,pfx}' \
  -g '!**/{id_rsa,id_ed25519,.npmrc,.netrc,.pgpass}' -g '!**/*.tfstate*' \
  -e '@(Get|Post|Put|Delete|Patch|Request)Mapping|\[Http(Get|Post|Put|Delete|Patch)\]|app\.(get|post|put|delete)\(|router\.(get|post|put|delete)\(|HandleFunc|@app\.route|def (main|handler)\(' "$repo" | head -100
```

Adapt the pattern to the detected stack. Open a listed file and record the handler location, not
just the route.

## Search hygiene

- Exclude `.git`, dependency directories, build output, binaries, key material (`*.pem`,
  `*.key`, `*.p12`), credential files (`.npmrc`, `.netrc`, `.pgpass`), and infrastructure state
  (`*.tfstate*`).
- Prefer `git ls-files` or `rg --files` over recursive `find`; both respect ignore rules.
- Bound output with `head` and record that the result was truncated.
- Prefer `rg -l` / `grep -l` for config-adjacent searches; never print matching lines from
  `.env`, secret stores, or credential files.
- Never run searches that print secret values or personal data.
- When a search result is used as evidence, quote the path and line range, not the whole file.
