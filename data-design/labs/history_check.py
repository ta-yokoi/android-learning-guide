"""Exhaustively check small histories of a single read/write register."""

from dataclasses import dataclass
from itertools import permutations


@dataclass(frozen=True)
class Operation:
    kind: str
    start: int
    end: int
    value: int


def linearizable(operations, initial):
    precedences = [
        (a, b) for a in range(len(operations)) for b in range(len(operations))
        if a != b and operations[a].end < operations[b].start
    ]
    for order in permutations(range(len(operations))):
        position = {index: step for step, index in enumerate(order)}
        if any(position[a] >= position[b] for a, b in precedences):
            continue
        value = initial
        for index in order:
            event = operations[index]
            if event.kind == "write":
                value = event.value
            elif event.value != value:
                break
        else:
            return True
    return False


def main():
    write = Operation("write", 1, 4, 1200)
    overlapping = Operation("read", 2, 5, 1000)
    later = Operation("read", 5, 6, 1000)
    allowed = linearizable([write, overlapping], initial=1000)
    rejected = linearizable([write, later], initial=1000)
    assert allowed and not rejected
    print("overlapping old read:", allowed)
    print("later old read:", rejected)


if __name__ == "__main__":
    main()
