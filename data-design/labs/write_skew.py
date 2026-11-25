"""An explicit schedule without same-row conflicts breaks an invariant."""

def request_leave(worker, read_view):
    return worker if sum(read_view.values()) >= 2 else None


def main():
    starting = {"A": True, "B": True}
    read_view = starting.copy()
    first = request_leave("A", read_view)
    second = request_leave("B", read_view)
    assert first == "A" and second == "B"
    snapshot = starting.copy()
    for worker in (first, second):
        snapshot[worker] = False

    serial = starting.copy()
    for worker in ("A", "B"):
        approved = request_leave(worker, serial)
        if approved is not None:
            serial[approved] = False
    assert sum(snapshot.values()) == 0 and sum(serial.values()) == 1
    print("same snapshot: on duty =", sum(snapshot.values()))
    print("serial evaluation: on duty =", sum(serial.values()))


if __name__ == "__main__":
    main()
