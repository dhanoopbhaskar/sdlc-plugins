#!/usr/bin/env python3
"""Validate a DevLoop investigation report.

An investigation report is the durable output of the `investigate` skill: a
demonstrated cause, the evidence that excludes the alternatives, the fix, and
the proof that the fix changes the failure. This module validates the structure
and the evidence rules, not the truth of the cause — the Gate D fixture runner
ties a reference report to a repository where the bug can actually be seen.

Usage:

    python3 evals/investigation.py .sdlc/investigations/<slug>/report.md

Exit codes: 0 = valid; 1 = invalid.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import verdict as verdict_mod

SCHEMA = "sdlc.investigation/v1"
CONFIDENCE = {"confirmed", "unconfirmed"}
PROOF_KINDS = {"REGRESSION-TEST", "INFRA-PROOF", "FLAKY-PROOF"}
PROOF_FIELDS = {
    "REGRESSION-TEST": ("test", "before", "after", "suite"),
    "INFRA-PROOF": ("harness", "before", "after", "mechanism"),
    "FLAKY-PROOF": ("loop", "before", "after", "mechanism"),
}
FENCE_RE = re.compile(r"```json[ \t]*\n(.*?)\n```", re.S)
EVIDENCE_LOCATION_RE = re.compile(r"\S+:\d+(?:-\d+)?")


class InvestigationError(ValueError):
    """Raised when an investigation report is structurally invalid."""


def extract_json(text: str) -> dict:
    """Return the last fenced ```json block in a Markdown report."""
    matches = FENCE_RE.findall(text)
    if not matches:
        raise InvestigationError("no ```json fenced block found")
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError as exc:
        raise InvestigationError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InvestigationError("the investigation block must be a JSON object")
    return data


def _require_string(obj: dict, key: str, where: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvestigationError(f"{where}: {key!r} must be a non-empty string")
    return value


def _require_strings(obj: dict, key: str, where: str, *, non_empty: bool) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise InvestigationError(f"{where}: {key!r} must be an array of non-empty strings")
    if non_empty and not value:
        raise InvestigationError(f"{where}: {key!r} must not be empty")
    return value


def _check_proof(proof: object) -> None:
    if not isinstance(proof, dict):
        raise InvestigationError("proof must be an object")
    kind = _require_string(proof, "kind", "proof")
    if kind not in PROOF_KINDS:
        raise InvestigationError(f"proof.kind must be one of {sorted(PROOF_KINDS)}")
    for key in PROOF_FIELDS[kind]:
        _require_string(proof, key, "proof")


def validate(report: dict) -> None:
    """Validate the report structure. Raises InvestigationError on failure."""
    if report.get("schema") != SCHEMA:
        raise InvestigationError(f"schema must be {SCHEMA!r}")
    _require_string(report, "diff_hash", SCHEMA)

    for key in ("symptom", "trigger", "cause"):
        _require_string(report, key, SCHEMA)

    evidence = _require_strings(report, "evidence", SCHEMA, non_empty=True)
    if not any(EVIDENCE_LOCATION_RE.search(item) for item in evidence):
        raise InvestigationError(
            "evidence must cite at least one concrete `file:line` location"
        )
    _require_strings(report, "alternatives", SCHEMA, non_empty=True)
    _require_strings(report, "fix", SCHEMA, non_empty=True)

    confidence = _require_string(report, "confidence", SCHEMA)
    if confidence not in CONFIDENCE:
        raise InvestigationError(f"confidence must be one of {sorted(CONFIDENCE)}")

    unproven = _require_strings(report, "unproven", SCHEMA, non_empty=False)
    if confidence == "unconfirmed" and not unproven:
        raise InvestigationError(
            "an unconfirmed cause must record at least one unproven item"
        )
    if confidence == "confirmed" and unproven:
        raise InvestigationError(
            "a confirmed cause cannot carry unproven items; mark it unconfirmed"
        )

    _check_proof(report.get("proof"))
    try:
        verdict_mod._check_redaction(report, SCHEMA)
    except verdict_mod.VerdictError as exc:
        raise InvestigationError(str(exc)) from exc


def check(report: dict) -> str:
    """Validate the report and return its proof kind."""
    validate(report)
    return report["proof"]["kind"]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 evals/investigation.py <report.md|report.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            data = extract_json(text)
        if not isinstance(data, dict):
            raise InvestigationError("the report must be a JSON object")
        kind = check(data)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1
    except InvestigationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {kind}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
