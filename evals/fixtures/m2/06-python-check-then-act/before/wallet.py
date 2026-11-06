class Wallet:
    def __init__(self, store):
        self.store = store

    def withdraw(self, account_id: str, amount: int) -> bool:
        updated = self.store.decrement_if_sufficient(account_id, amount)
        return updated == 1
