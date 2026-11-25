"""Model a storage boundary that atomically rejects older generations."""


class Shipment:
    def __init__(self):
        self.generation = 0
        self.state = "pending"

    def store(self, generation, state):
        # Treated as one atomic operation in this sequential model.
        if generation < self.generation:
            return False
        self.generation, self.state = generation, state
        return True


def main():
    shipment = Shipment()
    assert shipment.store(7, "packing")
    assert shipment.store(8, "handed-off")
    stale_accepted = shipment.store(7, "packing")
    assert not stale_accepted and shipment.state == "handed-off"
    print("generation:", shipment.generation)
    print("stale write accepted:", stale_accepted)
    print("shipment state:", shipment.state)


if __name__ == "__main__":
    main()
