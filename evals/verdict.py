#!/usr/bin/env python3
"""Validate a DevLoop verdict artifact and recompute its verdict.

Usage:

    python3 evals/verdict.py .sdlc/reviews/<slug>/verdict.md

Exit codes: 0 = valid and the declared verdict matches; 1 = invalid or mismatch.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCHEMA = "sdlc.verdict/v1"
SEVERITIES = {"P0", "P1", "P2", "P3"}
LENSES = {"L1", "L2", "L3"}
TIERS = {"T0", "T1", "T2"}
ISOLATION = {"isolated", "single-context"}
ACS = {"confirmed", "unconfirmed"}

FENCE_RE = re.compile(r"```json[ \t]*\n(.*?)\n```", re.S)
SECRET_RE = re.compile(
    r"(?:"
    r"sk_live_[A-Za-z0-9]{10,}"
    r"|sk_test_[A-Za-z0-9]{10,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|ghp_[A-Za-z0-9]{20,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r")"
)


class VerdictError(ValueError):
    """Raised when an artifact is structurally invalid or the verdict is wrong."""


def extract_json(text: str) -> dict:
    """Return the last fenced ```json block in a Markdown artifact."""
    matches = FENCE_RE.findall(text)
    if not matches:
        raise VerdictError("no ```json fenced block found")
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError as exc:
        raise VerdictError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise VerdictError("the verdict block must be a JSON object")
    return data


def _require_string(obj: dict, key: str, where: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise VerdictError(f"{where}: {key!r} must be a non-empty string")
    return value


def _require_list(obj: dict, key: str, where: str) -> list:
    value = obj.get(key)
    if not isinstance(value, list):
        raise VerdictError(f"{where}: {key!r} must be an array")
    return value


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def _check_redaction(value, where: str) -> None:
    for text in _walk_strings(value):
        match = SECRET_RE.search(text)
        if match is not None:
            raise VerdictError(
                f"{where}: possible secret value {match.group(0)[:12]!r}…; "
                "redact it and cite the path and line instead"
            )


def _check_findings(findings: list) -> None:
    seen: set[str] = set()
    for index, finding in enumerate(findings):
        where = f"findings[{index}]"
        if not isinstance(finding, dict):
            raise VerdictError(f"{where}: must be an object")
        finding_id = _require_string(finding, "id", where)
        if finding_id in seen:
            raise VerdictError(f"{where}: duplicate finding id {finding_id!r}")
        seen.add(finding_id)

        lens = _require_string(finding, "lens", where)
        if lens not in LENSES:
            raise VerdictError(f"{where}: lens must be one of {sorted(LENSES)}")
        severity = _require_string(finding, "severity", where)
        if severity not in SEVERITIES:
            raise VerdictError(f"{where}: severity must be one of {sorted(SEVERITIES)}")
        _require_string(finding, "file", where)
        line = finding.get("line")
        if isinstance(line, bool) or not isinstance(line, int) or line < 1:
            raise VerdictError(f"{where}: 'line' must be a positive integer")
        for key in ("trigger", "consequence", "fix"):
            _require_string(finding, key, where)

        absence = finding.get("absence", False)
        if not isinstance(absence, bool):
            raise VerdictError(f"{where}: 'absence' must be a boolean")
        if absence:
            _require_string(finding, "absence_of", where)

        accepted = finding.get("accepted_risk", False)
        if not isinstance(accepted, bool):
            raise VerdictError(f"{where}: 'accepted_risk' must be a boolean")
        if accepted:
            acceptance = finding.get("risk_acceptance")
            if not isinstance(acceptance, dict):
                raise VerdictError(f"{where}: accepted_risk requires 'risk_acceptance'")
            for key in ("approver", "date", "rationale"):
                _require_string(acceptance, key, f"{where}.risk_acceptance")
        _check_redaction(finding, where)


def validate(verdict: dict) -> None:
    """Validate the artifact structure. Raises VerdictError on failure."""
    if verdict.get("schema") != SCHEMA:
        raise VerdictError(f"schema must be {SCHEMA!r}")
    for key in ("base_sha", "diff_hash", "profile_hash"):
        _require_string(verdict, key, SCHEMA)

    tier = _require_string(verdict, "tier", SCHEMA)
    if tier not in TIERS:
        raise VerdictError(f"tier must be one of {sorted(TIERS)}")
    isolation = _require_string(verdict, "isolation", SCHEMA)
    if isolation not in ISOLATION:
        raise VerdictError(f"isolation must be one of {sorted(ISOLATION)}")
    acs = _require_string(verdict, "acs", SCHEMA)
    if acs not in ACS:
        raise VerdictError(f"acs must be one of {sorted(ACS)}")

    findings = _require_list(verdict, "findings", SCHEMA)
    _check_findings(findings)

    unproven = _require_list(verdict, "unproven", SCHEMA)
    for index, item in enumerate(unproven):
        where = f"unproven[{index}]"
        if not isinstance(item, dict):
            raise VerdictError(f"{where}: must be an object")
        _require_string(item, "item", where)
        if not isinstance(item.get("accepted"), bool):
            raise VerdictError(f"{where}: 'accepted' must be a boolean")
        if "reason" in item:
            _require_string(item, "reason", where)

    coverage = _require_list(verdict, "coverage_gaps", SCHEMA)
    unproven_items = {item["item"] for item in unproven}
    for index, gap in enumerate(coverage):
        where = f"coverage_gaps[{index}]"
        if not isinstance(gap, dict):
            raise VerdictError(f"{where}: must be an object")
        lens = _require_string(gap, "lens", where)
        if lens not in LENSES:
            raise VerdictError(f"{where}: lens must be one of {sorted(LENSES)}")
        item = _require_string(gap, "item", where)
        if not isinstance(gap.get("t2_relevant"), bool):
            raise VerdictError(f"{where}: 't2_relevant' must be a boolean")
        if gap["t2_relevant"] and item not in unproven_items:
            raise VerdictError(
                f"{where}: T2-relevant coverage gap {item!r} must appear in 'unproven'"
            )

    blocked_env = _require_list(verdict, "blocked_env", SCHEMA)
    for index, value in enumerate(blocked_env):
        if not isinstance(value, str) or not value.strip():
            raise VerdictError(f"blocked_env[{index}]: must be a non-empty string")

    signoff = verdict.get("signoff")
    if signoff is not None:
        if not isinstance(signoff, dict):
            raise VerdictError("signoff must be an object or null")
        for key in ("approver", "date", "scope"):
            _require_string(signoff, key, "signoff")

    _require_string(verdict, "verdict", SCHEMA)
    _check_redaction(verdict, SCHEMA)


def compute(verdict: dict) -> str:
    """Recompute the verdict string from the artifact's facts."""
    findings = verdict["findings"]
    live = [finding for finding in findings if not finding.get("accepted_risk", False)]
    accepted_any = any(finding.get("accepted_risk", False) for finding in findings)

    if any(finding["severity"] == "P0" for finding in live):
        return "BLOCK"
    if any(finding["severity"] == "P1" for finding in live):
        return "FIX"
    if verdict["blocked_env"]:
        return "BLOCKED-ENV"
    if verdict["acs"] != "confirmed":
        return "UNSCOPED"
    if verdict["tier"] == "T2" and verdict["isolation"] != "isolated":
        return "BLOCKED-UNVERIFIED"
    if any(not item["accepted"] for item in verdict["unproven"]):
        return "BLOCKED-UNVERIFIED"
    if verdict["tier"] == "T2" and verdict.get("signoff") is None:
        return "AWAITING-SIGNOFF"

    qualifiers: list[str] = []
    if verdict["isolation"] != "isolated":
        qualifiers.append("SINGLE-CONTEXT")
    if verdict.get("signoff") is not None:
        qualifiers.append("SIGNED")
    if accepted_any:
        qualifiers.append("RISK-ACCEPTED")
    if qualifiers:
        return f"MERGE-READY ({', '.join(qualifiers)})"
    return "MERGE-READY"


def check(verdict: dict) -> str:
    """Validate the artifact and enforce that its declared verdict is correct."""
    validate(verdict)
    declared = verdict["verdict"]
    computed = compute(verdict)
    if declared != computed:
        raise VerdictError(
            f"declared verdict {declared!r} does not match computed {computed!r}"
        )
    return computed


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 evals/verdict.py <verdict.md|verdict.json>", file=sys.stderr)
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
            raise VerdictError("the artifact must be a JSON object")
        result = check(data)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1
    except VerdictError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
