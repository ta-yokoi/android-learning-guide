"""Trace a two-phase commit participant after the coordinator crashes."""
from dataclasses import dataclass


@dataclass
class Participant:
    state: str = "open"

    def prepare(self):
        assert self.state == "open"
        self.state = "prepared"

    def learn(self, decision):
        assert decision in ("committed", "aborted")
        assert self.state in ("prepared", decision)
        self.state = decision


def main():
    inventory, reservation = Participant(), Participant()
    inventory.prepare()
    reservation.prepare()
    # Model the coordinator flushing its decision before sending it.
    durable_decision = {"order-42": "committed"}
    inventory.learn(durable_decision["order-42"])
    # The coordinator stops before sending the second notification.
    assert reservation.state == "prepared"
    print("during outage:", inventory.state, reservation.state)
    recovered = durable_decision["order-42"]
    for participant in (inventory, reservation):
        participant.learn(recovered)
    assert inventory.state == reservation.state == "committed"
    print("after replay:", inventory.state, reservation.state)
    try:
        reservation.learn("aborted")
    except AssertionError:
        print("conflicting decision: rejected")
    else:
        raise AssertionError("conflicting decision accepted")


if __name__ == "__main__":
    main()
