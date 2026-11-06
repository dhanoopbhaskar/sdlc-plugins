"""Tests for the verdict artifact parser and arithmetic."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verdict as v  # noqa: E402


def artifact(**overrides) -> dict:
    data = {
        "schema": "sdlc.verdict/v1",
        "base_sha": "a" * 40,
        "diff_hash": "sha256:" + "b" * 64,
        "profile_hash": "sha256:" + "c" * 64,
        "tier": "T1",
        "isolation": "isolated",
        "acs": "confirmed",
        "findings": [],
        "unproven": [],
        "coverage_gaps": [],
        "blocked_env": [],
        "signoff": None,
        "verdict": "MERGE-READY",
    }
    data.update(overrides)
    return data


def finding(**overrides) -> dict:
    data = {
        "id": "P1-001",
        "lens": "L1",
        "severity": "P1",
        "file": "src/app.py",
        "line": 10,
        "trigger": "a retry after a timeout",
        "consequence": "the write happens twice",
        "fix": "key the write by request id",
        "absence": False,
        "accepted_risk": False,
    }
    data.update(overrides)
    return data


def signoff() -> dict:
    return {"approver": "reviewer", "date": "2026-11-06", "scope": "T2 auth change"}


class ComputeTests(unittest.TestCase):
    def test_merge_ready(self) -> None:
        self.assertEqual(v.check(artifact()), "MERGE-READY")

    def test_single_context(self) -> None:
        data = artifact(isolation="single-context", verdict="MERGE-READY (SINGLE-CONTEXT)")
        self.assertEqual(v.check(data), "MERGE-READY (SINGLE-CONTEXT)")

    def test_p0_blocks(self) -> None:
        data = artifact(findings=[finding(severity="P0")], verdict="BLOCK")
        self.assertEqual(v.check(data), "BLOCK")

    def test_p1_fixes(self) -> None:
        data = artifact(findings=[finding(severity="P1")], verdict="FIX")
        self.assertEqual(v.check(data), "FIX")

    def test_accepted_p0(self) -> None:
        data = artifact(
            findings=[
                finding(
                    severity="P0",
                    accepted_risk=True,
                    risk_acceptance={
                        "approver": "owner",
                        "date": "2026-11-06",
                        "rationale": "compensating control in the gateway",
                    },
                )
            ],
            verdict="MERGE-READY (RISK-ACCEPTED)",
        )
        self.assertEqual(v.check(data), "MERGE-READY (RISK-ACCEPTED)")

    def test_accepted_p0_requires_record(self) -> None:
        data = artifact(findings=[finding(severity="P0", accepted_risk=True)], verdict="MERGE-READY")
        with self.assertRaisesRegex(v.VerdictError, "risk_acceptance"):
            v.check(data)

    def test_blocked_env(self) -> None:
        data = artifact(blocked_env=["DATABASE_URL is not set"], verdict="BLOCKED-ENV")
        self.assertEqual(v.check(data), "BLOCKED-ENV")

    def test_unscoped(self) -> None:
        data = artifact(acs="unconfirmed", verdict="UNSCOPED")
        self.assertEqual(v.check(data), "UNSCOPED")

    def test_unproven_blocks(self) -> None:
        data = artifact(
            unproven=[{"item": "load test", "accepted": False, "reason": "no env"}],
            verdict="BLOCKED-UNVERIFIED",
        )
        self.assertEqual(v.check(data), "BLOCKED-UNVERIFIED")

    def test_accepted_unproven_passes(self) -> None:
        data = artifact(
            unproven=[{"item": "load test", "accepted": True, "reason": "deferred"}],
            verdict="MERGE-READY",
        )
        self.assertEqual(v.check(data), "MERGE-READY")

    def test_t2_requires_isolation(self) -> None:
        data = artifact(tier="T2", isolation="single-context", signoff=signoff(), verdict="BLOCKED-UNVERIFIED")
        self.assertEqual(v.check(data), "BLOCKED-UNVERIFIED")

    def test_t2_awaiting_signoff(self) -> None:
        data = artifact(tier="T2", isolation="isolated", verdict="AWAITING-SIGNOFF")
        self.assertEqual(v.check(data), "AWAITING-SIGNOFF")

    def test_t2_signed(self) -> None:
        data = artifact(tier="T2", isolation="isolated", signoff=signoff(), verdict="MERGE-READY (SIGNED)")
        self.assertEqual(v.check(data), "MERGE-READY (SIGNED)")

    def test_t2_signed_and_risk_accepted(self) -> None:
        data = artifact(
            tier="T2",
            isolation="isolated",
            signoff=signoff(),
            findings=[
                finding(
                    severity="P1",
                    accepted_risk=True,
                    risk_acceptance={
                        "approver": "owner",
                        "date": "2026-11-06",
                        "rationale": "tracked in TICKET-1",
                    },
                )
            ],
            verdict="MERGE-READY (SIGNED, RISK-ACCEPTED)",
        )
        self.assertEqual(v.check(data), "MERGE-READY (SIGNED, RISK-ACCEPTED)")

    def test_p0_beats_accepted_p1(self) -> None:
        data = artifact(
            findings=[
                finding(id="P0-001", severity="P0"),
                finding(
                    id="P1-001",
                    severity="P1",
                    accepted_risk=True,
                    risk_acceptance={
                        "approver": "owner",
                        "date": "2026-11-06",
                        "rationale": "accepted",
                    },
                ),
            ],
            verdict="BLOCK",
        )
        self.assertEqual(v.check(data), "BLOCK")


class ValidationTests(unittest.TestCase):
    def test_mismatch_is_rejected(self) -> None:
        data = artifact(findings=[finding(severity="P0")], verdict="MERGE-READY")
        with self.assertRaisesRegex(v.VerdictError, "does not match"):
            v.check(data)

    def test_finding_requires_trigger(self) -> None:
        data = artifact(findings=[finding(trigger="")], verdict="FIX")
        with self.assertRaisesRegex(v.VerdictError, "trigger"):
            v.check(data)

    def test_absence_requires_absence_of(self) -> None:
        data = artifact(findings=[finding(absence=True)], verdict="FIX")
        with self.assertRaisesRegex(v.VerdictError, "absence_of"):
            v.check(data)

    def test_t2_coverage_gap_must_be_unproven(self) -> None:
        data = artifact(
            tier="T2",
            signoff=signoff(),
            coverage_gaps=[{"lens": "L3", "item": "load test", "t2_relevant": True}],
            verdict="MERGE-READY (SIGNED)",
        )
        with self.assertRaisesRegex(v.VerdictError, "must appear in 'unproven'"):
            v.check(data)

    def test_secret_is_rejected(self) -> None:
        data = artifact(
            findings=[finding(trigger="token sk_live_abcdefghijklmnop leaked")],
            verdict="FIX",
        )
        with self.assertRaisesRegex(v.VerdictError, "possible secret"):
            v.check(data)

    def test_duplicate_finding_id(self) -> None:
        data = artifact(
            findings=[finding(id="P1-001"), finding(id="P1-001")],
            verdict="FIX",
        )
        with self.assertRaisesRegex(v.VerdictError, "duplicate finding id"):
            v.check(data)

    def test_bad_severity(self) -> None:
        data = artifact(findings=[finding(severity="P9")], verdict="FIX")
        with self.assertRaisesRegex(v.VerdictError, "severity"):
            v.check(data)

    def test_bad_line(self) -> None:
        data = artifact(findings=[finding(line=0)], verdict="FIX")
        with self.assertRaisesRegex(v.VerdictError, "positive integer"):
            v.check(data)


class ExtractionTests(unittest.TestCase):
    def test_extract_last_fenced_block(self) -> None:
        text = "# Verdict\n\n```json\n{\"a\": 1}\n```\n\nlater\n\n```json\n{\"b\": 2}\n```\n"
        self.assertEqual(v.extract_json(text), {"b": 2})

    def test_no_fenced_block(self) -> None:
        with self.assertRaisesRegex(v.VerdictError, "no ```json"):
            v.extract_json("# Verdict\n\nnothing here\n")

    def test_malformed_json(self) -> None:
        with self.assertRaisesRegex(v.VerdictError, "invalid JSON"):
            v.extract_json("```json\n{not json}\n```")

    def test_non_object_block(self) -> None:
        with self.assertRaisesRegex(v.VerdictError, "JSON object"):
            v.extract_json("```json\n[1, 2]\n```")

    def test_full_markdown_artifact(self) -> None:
        data = artifact()
        text = f"# Verdict\n\nMERGE-READY\n\n```json\n{json.dumps(data)}\n```\n"
        self.assertEqual(v.check(v.extract_json(text)), "MERGE-READY")


if __name__ == "__main__":
    unittest.main()
