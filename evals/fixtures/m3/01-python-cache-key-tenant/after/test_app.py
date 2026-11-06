import unittest

from app import Cache, load_profile


class TenantCacheTest(unittest.TestCase):
    def test_same_user_in_different_tenants_does_not_share(self):
        cache = Cache()
        first = load_profile(cache, "tenant-a", 7, lambda: {"tenant": "tenant-a"})
        second = load_profile(cache, "tenant-b", 7, lambda: {"tenant": "tenant-b"})
        self.assertEqual(first["tenant"], "tenant-a")
        self.assertEqual(second["tenant"], "tenant-b")


if __name__ == "__main__":
    unittest.main()
