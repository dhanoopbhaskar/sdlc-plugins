#!/usr/bin/env python3
"""Measure the context budget for the core install and the gate.

Token counts are an estimate (``ceil(characters / 4)``); no tokenizer dependency
is used. Use the same estimate when comparing before and after.

    python3 evals/measure.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "plugins" / "sdlc"
GATE = CORE / "skills" / "merge-gate"

CORE_DESCRIPTION_TARGET = 275
STATIC_GATE_TARGET = 15_000

DESCRIPTION_RE = re.compile(r'^description:[ \t]*(.*)$', re.M)


def estimate_tokens(text: str) -> int:
    """Estimate tokens as ceil(characters / 4)."""
    return math.ceil(len(text) / 4) if text else 0


def description(skill_md: Path) -> str:
    match = DESCRIPTION_RE.search(skill_md.read_text(encoding="utf-8"))
    if match is None:
        return ""
    value = match.group(1).strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value


def core_descriptions() -> list[tuple[str, str]]:
    skills = CORE / "skills"
    return [
        (path.name, description(path / "SKILL.md"))
        for path in sorted(skills.iterdir())
        if (path / "SKILL.md").is_file()
    ]


def read(*parts: str) -> str:
    return (GATE.joinpath(*parts)).read_text(encoding="utf-8")


def static_budgets() -> list[tuple[str, str]]:
    skill = read("SKILL.md")
    return [
        ("always: SKILL.md", skill),
        (
            "phase 1: SKILL + scope + profile",
            skill + read("references", "scope.md") + read("references", "profile.md"),
        ),
        (
            "phase 2: SKILL + proof + profile",
            skill + read("references", "proof.md") + read("references", "profile.md"),
        ),
        (
            "one lens pass: SKILL + lens + evidence",
            skill
            + read("references", "lens-l1.md")
            + read("references", "evidence.md"),
        ),
        (
            "phase 4: SKILL + merge + verdict schema",
            skill
            + read("references", "merge.md")
            + read("references", "verdict-schema.md"),
        ),
        (
            "full static set (one lens at a time)",
            skill
            + read("references", "scope.md")
            + read("references", "proof.md")
            + read("references", "profile.md")
            + read("references", "isolation.md")
            + read("references", "evidence.md")
            + read("references", "merge.md")
            + read("references", "verdict-schema.md")
            + read("references", "lens-l1.md"),
        ),
    ]


def main() -> int:
    failures: list[str] = []

    print("Core install descriptions (always-on)")
    print("=" * 38)
    total = 0
    for name, text in core_descriptions():
        tokens = estimate_tokens(text)
        total += tokens
        print(f"{name:<28} {len(text):>5} chars  ~{tokens:>4} tokens")
    print(f"{'total':<28} {'':>5}        ~{total:>4} tokens")
    print(f"target: <= {CORE_DESCRIPTION_TARGET} tokens")
    if total > CORE_DESCRIPTION_TARGET:
        failures.append(
            f"core descriptions estimate {total} tokens, over {CORE_DESCRIPTION_TARGET}"
        )

    print()
    print("Gate static context (estimate; diff, ACs, and proof are additional)")
    print("=" * 70)
    for label, text in static_budgets():
        tokens = estimate_tokens(text)
        print(f"{label:<52} {len(text):>6} chars  ~{tokens:>5} tokens")
    static_total = estimate_tokens(static_budgets()[-1][1])
    print(f"target: <= {STATIC_GATE_TARGET} tokens for the static set")
    if static_total > STATIC_GATE_TARGET:
        failures.append(
            f"gate static context estimates {static_total} tokens, "
            f"over {STATIC_GATE_TARGET}"
        )

    print()
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print("PASS: context budgets are within target")
    return 0


if __name__ == "__main__":
    sys.exit(main())
