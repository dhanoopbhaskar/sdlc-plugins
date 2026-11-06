class Wallet:
    def __init__(self, store):
        self.store = store

    def withdraw(self, account_id: str, amount: int) -> bool:
        balance = self.store.get_balance(account_id)
        if balance >= amount:
            self.store.set_balance(account_id, balance - amount)
            return True
        return False
