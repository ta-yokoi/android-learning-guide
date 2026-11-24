"""Simulate a provider committing a payment before its first reply is lost."""


class ProviderModel:
    def __init__(self):
        self.payments = {}

    def charge(self, key, amount_yen, *, lose_reply=False):
        if key in self.payments:
            previous_amount, receipt = self.payments[key]
            if previous_amount != amount_yen:
                raise ValueError("key reused with a different amount")
        else:
            receipt = f"payment-{len(self.payments) + 1}"
            self.payments[key] = (amount_yen, receipt)
        if lose_reply:
            raise TimeoutError("reply lost after commit")
        return receipt


def main():
    provider = ProviderModel()
    key = "order-42:payment-1"
    try:
        provider.charge(key, 1200, lose_reply=True)
    except TimeoutError:
        print("first reply: unknown")
    receipt = provider.charge(key, 1200)
    assert receipt == "payment-1" and len(provider.payments) == 1
    print("retry receipt:", receipt)
    print("payment count:", len(provider.payments))
    try:
        provider.charge(key, 1500)
    except ValueError:
        print("changed amount: conflict")
    else:
        raise AssertionError("different amount accepted")


if __name__ == "__main__":
    main()
