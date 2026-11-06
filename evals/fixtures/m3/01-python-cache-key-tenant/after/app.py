class Cache:
    """A tiny in-process cache."""

    def __init__(self):
        self._store = {}

    def get_or_compute(self, key, compute):
        if key not in self._store:
            self._store[key] = compute()
        return self._store[key]


def load_profile(cache, tenant_id, user_id, fetch):
    return cache.get_or_compute((tenant_id, user_id), fetch)
