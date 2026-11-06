# Typo-tolerant config silently disables TLS (YAML/Python)

**Fixture:** `m2/08-yaml-unsafe-default`  
**Stack:** yaml  
**Tier:** T2  
**Expected verdict:** `FIX`

## Acceptance criteria

TLS is required unless an operator explicitly disables it, and a misspelled key is rejected.

## What the diff does

The loader reads a misspelled key and defaults TLS to off. A correct YAML file is ignored without error, so every environment silently downgrades.

## A correct pass must

- report a present P1 finding under L1 at `config.py:3`;
- return `FIX`, not a softer verdict;
- keep every finding tied to a concrete trigger.
