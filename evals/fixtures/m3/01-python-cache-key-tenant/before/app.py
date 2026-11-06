class Cache:
    """A tiny in-process cache."""

    def __init__(self):
        self._store = {}

    def get_or_compute(self, user_id, compute):
        if user_id not in self._store:
            self._store[user_id] = compute()
        return self._store[user_id]


def load_profile(cache, tenant_id, user_id, fetch):
    return cache.get_or_compute(user_id, fetch)
