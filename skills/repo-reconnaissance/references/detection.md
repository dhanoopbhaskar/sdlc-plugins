# Detection Signals

A signal is evidence, not proof. One file name is weak; a manifest plus a lockfile plus CI is
strong. Grade accordingly and always record the file you read.

## Repository topology

| Signal | Suggests |
| --- | --- |
| One manifest at root | Single project |
| Workspace manifest listing packages, or multiple manifests under one root with shared CI | Monorepo |
| `CODEOWNERS`, release tags, and CI per repository | Polyrepo |
| Submodules or a manifest that pins other repos | Hybrid; record each pinned repo separately |
| Multiple independent lockfiles with no shared workspace root | Polyrepo imported into one folder; treat as separate projects |

Do not rely on folder names such as `packages/`, `apps/`, or `services/`. Confirm with the
workspace declaration and the CI matrix.

## Language and runtime manifests

| Category | Typical evidence |
| --- | --- |
| JavaScript / TypeScript | `package.json`, lockfiles, `tsconfig*.json`, workspace config |
| Python | `pyproject.toml`, `requirements*.txt`, `setup.py`, `Pipfile`, `poetry.lock`, `uv.lock` |
| JVM | `pom.xml`, `build.gradle*`, `settings.gradle*`, `gradle.properties`, `*.jar` manifests |
| .NET | `*.sln`, `*.csproj`, `*.fsproj`, `global.json`, `packages.lock.json`, `Directory.Build.props` |
| Go | `go.mod`, `go.sum`, `vendor/modules.txt` |
| Rust | `Cargo.toml`, `Cargo.lock`, `rust-toolchain*` |
| Ruby | `Gemfile`, `Gemfile.lock`, `*.gemspec` |
| PHP | `composer.json`, `composer.lock` |
| Elixir / Erlang | `mix.exs`, `mix.lock`, `rebar.config` |
| Swift / Objective-C | `Package.swift`, `*.xcodeproj`, `Podfile`, `Cartfile` |
| Kotlin / Android | `build.gradle*`, `AndroidManifest.xml` |
| C / C++ | `CMakeLists.txt`, `Makefile`, `meson.build`, `conanfile.*`, `vcpkg.json` |
| Scala | `build.sbt`, `project/plugins.sbt` |
| Clojure | `deps.edn`, `project.clj` |
| Dart / Flutter | `pubspec.yaml`, `pubspec.lock` |
| R | `DESCRIPTION`, `renv.lock` |
| Perl | `cpanfile`, `Makefile.PL` |
| Haskell | `*.cabal`, `stack.yaml` |
| Shell / ops | `*.sh`, `*.ps1`, `Taskfile*`, `Makefile`, `justfile` |
| Data / analytics | `dbt_project.yml`, `*.sql` with migration conventions, notebooks |
| Infrastructure | `*.tf`, `*.bicep`, `Pulumi.yaml`, `template.yaml` (SAM/CloudFormation), Helm charts |
| Contracts | `*.proto`, `*.graphql`, `openapi.*`, `swagger.*`, `*.avsc`, `asyncapi.*` |

Version evidence, in order of authority: lockfile → runtime pin file / toolchain → container
base image → CI matrix → manifest range → README.

## Build and task entry points

| Signal | What it declares |
| --- | --- |
| CI workflow files | The commands that actually gate merges and releases |
| `Makefile`, `justfile`, `Taskfile`, `Rakefile`, `magefile`, `build.sh` | Project-defined tasks |
| Manifest `scripts` / plugin targets | Per-package tasks |
| Wrapper scripts (`mvnw`, `gradlew`, `dotnet` SDK pin, `uv`, `poetry`) | Preferred toolchain |
| Container build files | Build and runtime stages, exposed ports, entry command |
| `README` / `CONTRIBUTING` | Intended developer workflow; verify against CI |

When several disagree, CI wins for what is enforced, the wrapper wins for how to invoke it, and
the README is the weakest signal.

## Test and quality signals

- Test directories and naming conventions (`test`, `tests`, `spec`, `__tests__`, `*_test.*`,
  `*.spec.*`, `*.Tests`).
- Test runner configuration and coverage thresholds.
- Snapshot/golden files and fixtures (behavior encoded as data).
- Contract tests, consumer-driven contracts, and schema validation.
- Static analysis and lint configuration.
- Mutation testing, property-based testing, and fuzzing configuration.
- Disabled or skipped tests (a risk signal, not an exclusion).

## Deployment and runtime

| Signal | Suggests |
| --- | --- |
| `Dockerfile`, `Containerfile`, `.dockerignore` | Containerized deployable |
| Compose files | Local or single-host topology; reveals dependencies |
| Kubernetes manifests / Helm / Kustomize | Orchestrated services, jobs, cron |
| Serverless config | Functions, triggers, managed bindings |
| PaaS config | Buildpack/runtime target |
| IaC | Provisioned infrastructure, environments, data stores |
| CI/CD release jobs | Artifact type, registry, promotion path |
| `Procfile`, systemd units, init scripts | Process model, long-running workers |
| Schedules / cron / workflow definitions | Batch and periodic behavior |
| Feature flag config | Runtime branching that tests may not cover |

## Data and messaging

- ORM models, entity mappings, and migration directories.
- Schema dumps, `.sql` files, stored procedures, views, triggers.
- Connection configuration and pool settings (record key names, never values).
- Search indexes, caches, object storage, and file shares.
- Queue/topic declarations, consumer groups, subscriptions, dead-letter configuration.
- CDC, ETL, and warehouse loaders.
- Serialization schemas and versioning conventions.

## External integrations

- HTTP client wrappers and generated API clients.
- SDK dependencies for identity, payments, email, storage, and observability.
- Webhooks in and out.
- File drops, SFTP, shared drives, and batch exchange directories.
- Shared databases used as an integration mechanism (a high-risk boundary).
- Hard-coded hostnames, endpoints, and environment switches.

## Generated code

Evidence that a file is generated, not authored:

- Header comment: "generated", "do not edit", "auto-generated", tool name and version.
- Location under a generator output directory.
- Paired generator config or template.
- Source file alongside with a matching name and a different extension.
- Presence in ignore files or build cleanup scripts.
- Consistent machine-like formatting and no history of hand edits.

Keep generated code in scope for **inventory** (it is part of the build and may encode
contracts) but exclude it from behavioral deep dives and from the first-party shard
denominator. Record it in the ledger `# Inventory-only` table: what generates it, from which
inputs, and whether the generator runs during the build.

## Vendored and third-party code

- Dependency directories committed to the repository.
- Submodules and pinned forks.
- License headers from another project.
- Copied sources with local modifications (check history and diff against upstream if cheap).
- Patch files and vendor manifests.

Vendored code is a migration risk in its own right: record the upstream, the version, and
whether local patches must be carried forward.

## Archived or unused code

- No commits in the last 24 months (weaker signal; check deployment references).
- No references from build, CI, routes, or deployment config.
- README or docs state it is retired.
- Duplicate of another module with a "new"/"old" naming pair.
- Tests excluded from CI.

Record it as `skipped` in the ledger shard status or exclusion note, with evidence. Never delete
or exclude silently.

## Unknown stacks

If no known manifest matches:

1. Read the root README, build scripts, and CI — the project usually declares its own toolchain.
2. Look for a container base image that names the runtime.
3. Inspect file extensions and shebangs; confirm with an import or include statement.
4. Search for compiler/interpreter invocations in scripts.
5. Record `stack: unknown` with the evidence and an open question. Do not guess a language
   from one file.

Unknown is an acceptable outcome. A wrong assumption is not.
