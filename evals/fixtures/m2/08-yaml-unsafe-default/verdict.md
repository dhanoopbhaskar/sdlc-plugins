# Verdict — m2/08-yaml-unsafe-default

The loader reads a misspelled key and defaults TLS to off. A correct YAML file is ignored without error, so every environment silently downgrades.

## Findings

### P1-001 · L1 · config.py:3

Trigger:     a deployment whose config.yml correctly sets require_tls: true
Consequence: the misspelled key is never read and the unsafe False default wins, so TLS is off with no error
Fix:         read require_tls, default to True, and reject unknown config keys

## Coverage

- Checked: defaults, config parsing, typo tolerance.
- Checked: TLS configuration crosses a security boundary; recorded as also: L2.
- Checked: per-environment drift; the typo affects every environment.

## Verdict block

```json
{
  "schema": "sdlc.verdict/v1",
  "base_sha": "fixture-08-yaml-unsafe-default",
  "diff_hash": "sha256:837db6363e7fef2cfaaf81b431a83809a0fb1a1f2040453bb128fcfbc63f3401",
  "profile_hash": "sha256:none",
  "tier": "T2",
  "isolation": "isolated",
  "acs": "confirmed",
  "findings": [
    {
      "id": "P1-001",
      "lens": "L1",
      "severity": "P1",
      "file": "config.py",
      "line": 3,
      "trigger": "a deployment whose config.yml correctly sets require_tls: true",
      "consequence": "the misspelled key is never read and the unsafe False default wins, so TLS is off with no error",
      "fix": "read require_tls, default to True, and reject unknown config keys",
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
