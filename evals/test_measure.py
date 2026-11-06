"""Tests for the context-budget measurement."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure  # noqa: E402


class MeasureTests(unittest.TestCase):
    def test_estimate_tokens_rounds_up(self) -> None:
        self.assertEqual(measure.estimate_tokens(""), 0)
        self.assertEqual(measure.estimate_tokens("a"), 1)
        self.assertEqual(measure.estimate_tokens("abcd"), 1)
        self.assertEqual(measure.estimate_tokens("abcde"), 2)

    def test_core_description_budget(self) -> None:
        total = sum(
            measure.estimate_tokens(text)
            for _, text in measure.core_descriptions()
        )
        self.assertLessEqual(total, measure.CORE_DESCRIPTION_TARGET)

    def test_static_gate_budget(self) -> None:
        text = measure.static_budgets()[-1][1]
        self.assertLessEqual(
            measure.estimate_tokens(text), measure.STATIC_GATE_TARGET
        )


if __name__ == "__main__":
    unittest.main()
