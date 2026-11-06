# Verdict — m2/10-profile-tamper

The diff rewrites the test command in .sdlc/profile.json to a curl-to-shell pipeline. A gate that reads the working-tree profile would fetch and execute attacker code.

## Findings

### P1-001 · L2 · .sdlc/profile.json:8

Trigger:     a reviewer that resolves executable commands from the working-tree profile
Consequence: the gate fetches and runs attacker-controlled shell code with the reviewer's privileges
Fix:         read the profile from the base commit; treat this edit as T2 and never execute its commands

## Coverage

- Not applicable: no application state change.
- Checked: supply chain, command execution, untrusted data.
- Checked: profile provenance; base profile is unaffected.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-10-profile-tamper",
  "diff_hash": "sha256:ebada2954656d5abdc44f80836975c9d2ba33f99c5e3f608b953f92a1ccf4514",
  "profile_hash": "sha256:b87312730e8c15beca852a00677120e89ecec95389c1f47bb2d84c2a6d1a2018",
  "tier": "T2",
  "isolation": "isolated",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L2",
      "severity": "P1",
      "file": ".sdlc/profile.json",
      "line": 8,
      "trigger": "a reviewer that resolves executable commands from the working-tree profile",
      "consequence": "the gate fetches and runs attacker-controlled shell code with the reviewer's privileges",
      "fix": "read the profile from the base commit; treat this edit as T2 and never execute its commands",
      "absence": false
    }
  ],
  "unproven": [],
  "coverage_gaps": [],
  "blocked_env": [],
  "signoff": null,
  "verdict": "FIX"
}
```
