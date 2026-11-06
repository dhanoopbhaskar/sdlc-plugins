import unittest

from app import page


class PaginationTest(unittest.TestCase):
    def test_full_page_returns_size_items(self):
        self.assertEqual(page(list(range(10)), 1, 4), [0, 1, 2, 3])

    def test_last_partial_page(self):
        self.assertEqual(page(list(range(10)), 3, 4), [8, 9])


if __name__ == "__main__":
    unittest.main()
