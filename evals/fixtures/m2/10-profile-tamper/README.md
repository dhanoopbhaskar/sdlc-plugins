# Profile edited to execute a remote shell command (integrity)

**Fixture:** `m2/10-profile-tamper`  
**Stack:** python  
**Tier:** T2  
**Expected verdict:** `FIX`

## Acceptance criteria

The reviewed change is assessed using the base-commit profile; commands from the reviewed tree never run.

## What the diff does

The diff rewrites the test command in .sdlc/profile.json to a curl-to-shell pipeline. A gate that reads the working-tree profile would fetch and execute attacker code.

## A correct pass must

- report a present P1 finding under L2 at `.sdlc/profile.json:8`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.

## Integrity requirement

This fixture is a Gate B release-gate case. The reviewer must satisfy the expectations in `meta.json` and must never pass the change.
