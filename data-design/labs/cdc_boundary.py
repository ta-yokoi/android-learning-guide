"""Rebuild a projection across a snapshot/change-log handoff."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Change:
    position: int
    order: str
    amount: int


def rebuild(snapshot, position, changes):
    projection = snapshot.copy()
    for change in changes:
        if change.position <= position:
            continue  # The snapshot or an earlier delivery already included it.
        if change.position != position + 1:
            raise ValueError("missing log range")
        projection[change.order] = change.amount
        position = change.position
    return projection, position


def main():
    snapshot = {"order-42": 1200}
    log = [Change(4, "order-42", 1000), Change(5, "order-43", 800),
           Change(5, "order-43", 800), Change(6, "order-42", 1100)]
    projection, position = rebuild(snapshot, 4, log)
    assert projection == {"order-42": 1100, "order-43": 800} and position == 6
    print("last applied position:", position)
    print("projection total:", sum(projection.values()))
    try:
        rebuild(snapshot, 4, [log[-1]])
    except ValueError as error:
        print("gap:", error)
    else:
        raise AssertionError("missing position was accepted")


if __name__ == "__main__":
    main()
