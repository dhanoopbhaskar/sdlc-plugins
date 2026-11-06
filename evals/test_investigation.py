"""Tests for the investigation report validator and Gate D fixtures."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import investigation as inv  # noqa: E402
import run  # noqa: E402


def report(**overrides) -> dict:
    data = {
        "schema": "sdlc.investigation/v1",
        "diff_hash": "sha256:" + "a" * 64,
        "symptom": "the order is missing after a successful response",
        "trigger": "read immediately after the create response",
        "cause": "the insert is not awaited, so the response is sent before the write commits",
        "evidence": ["orders.py:42 — the promise is returned without await"],
        "alternatives": ["replica lag — the same connection reads the row when awaited"],
        "fix": ["orders.py: await the insert before building the response"],
        "proof": {
            "kind": "REGRESSION-TEST",
            "test": "tests/test_orders.py::test_read_after_create",
            "before": "exit 1 — expected 200, received 404",
            "after": "exit 0 — 1 passed",
            "suite": "exit 0 — 118 passed",
        },
        "confidence": "confirmed",
        "unproven": [],
    }
    data.update(overrides)
    return data


class ValidateTests(unittest.TestCase):
    def test_valid_report(self) -> None:
        self.assertEqual(inv.check(report()), "REGRESSION-TEST")

    def test_wrong_schema(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "schema"):
            inv.check(report(schema="sdlc.verdict/v1"))

    def test_cause_must_be_non_empty(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "cause"):
            inv.check(report(cause="  "))

    def test_evidence_requires_a_location(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "file:line"):
            inv.check(report(evidence=["the insert is not awaited"]))

    def test_alternatives_must_not_be_empty(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "alternatives"):
            inv.check(report(alternatives=[]))

    def test_unconfirmed_requires_unproven(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "unproven"):
            inv.check(report(confidence="unconfirmed"))

    def test_confirmed_rejects_unproven(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "confirmed"):
            inv.check(report(unproven=["load test not run"]))

    def test_unknown_proof_kind(self) -> None:
        data = report()
        data["proof"]["kind"] = "VIBES"
        with self.assertRaisesRegex(inv.InvestigationError, "proof.kind"):
            inv.check(data)

    def test_infra_proof_requires_harness(self) -> None:
        data = report()
        data["proof"] = {
            "kind": "INFRA-PROOF",
            "before": "8/10 failed",
            "after": "10/10 passed",
            "mechanism": "wait for the healthcheck",
        }
        with self.assertRaisesRegex(inv.InvestigationError, "harness"):
            inv.check(data)

    def test_flaky_proof_requires_loop(self) -> None:
        data = report()
        data["proof"] = {
            "kind": "FLAKY-PROOF",
            "before": "7/200 failed",
            "after": "0/200 failed",
            "mechanism": "the cache key includes the tenant",
        }
        with self.assertRaisesRegex(inv.InvestigationError, "loop"):
            inv.check(data)

    def test_redaction(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "secret"):
            inv.check(report(cause="the token sk_live_abcdefghijkl leaked"))

    def test_extract_json_uses_the_last_block(self) -> None:
        text = (
            "intro\n```json\n{\"old\": true}\n```\n"
            f"```json\n{json.dumps(report())}\n```\n"
        )
        self.assertEqual(inv.extract_json(text)["schema"], "sdlc.investigation/v1")

    def test_missing_block(self) -> None:
        with self.assertRaisesRegex(inv.InvestigationError, "fenced"):
            inv.extract_json("no block here")


class GateDTests(unittest.TestCase):
    def test_repository_fixtures_pass(self) -> None:
        ok, messages, count = run.run_gate_d()
        self.assertTrue(ok, "\n".join(messages))
        self.assertEqual(count, 3)

    def _copy_fixture(self, root: Path) -> Path:
        source = run.M3_FIXTURES / "01-python-cache-key-tenant"
        target = root / source.name
        shutil.copytree(source, target)
        return target

    def test_missing_cause_token_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = self._copy_fixture(Path(temp))
            report_path = fixture / "report.md"
            text = report_path.read_text(encoding="utf-8")
            original = inv.extract_json(text)["cause"]
            report_path.write_text(
                text.replace(original, "the returned value is wrong"),
                encoding="utf-8",
            )
            problems = run.check_investigation_fixture(fixture)
            self.assertTrue(any("does not name 'tenant'" in item for item in problems))

    def test_passing_before_fails_the_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = self._copy_fixture(Path(temp))
            fixed = (fixture / "after" / "app.py").read_text(encoding="utf-8")
            (fixture / "before" / "app.py").write_text(fixed, encoding="utf-8")
            problems = run.check_investigation_fixture(fixture)
            self.assertTrue(any("before/ tests pass" in item for item in problems))

    def test_wrong_diff_hash_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = self._copy_fixture(Path(temp))
            text = (fixture / "report.md").read_text(encoding="utf-8")
            (fixture / "report.md").write_text(
                text.replace("sha256:4a5db6", "sha256:000000"),
                encoding="utf-8",
            )
            problems = run.check_investigation_fixture(fixture)
            self.assertTrue(any("diff_hash" in item for item in problems))


if __name__ == "__main__":
    unittest.main()
