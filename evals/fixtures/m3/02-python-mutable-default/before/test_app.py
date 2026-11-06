import unittest

from app import add_tag


class MutableDefaultTest(unittest.TestCase):
    def test_calls_do_not_share_state(self):
        self.assertEqual(add_tag("a"), ["a"])
        self.assertEqual(add_tag("b"), ["b"])

    def test_explicit_list_is_used(self):
        tags = ["start"]
        self.assertIs(add_tag("next", tags), tags)
        self.assertEqual(tags, ["start", "next"])


if __name__ == "__main__":
    unittest.main()
