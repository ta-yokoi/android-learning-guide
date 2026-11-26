"""Deterministic vector search and finite-state fencing examples. Python 3.9+."""
import argparse
from collections import deque
from dataclasses import dataclass


VECTORS = {
    "a": (0, 0), "b": (4, 3), "c": (2, 2), "d": (4, 4),
    "e": (5, 4), "f": (2, 4), "g": (6, 6),
}
EDGES = {
    "a": ("b", "c"), "b": ("a", "d", "e"), "c": ("a", "f", "g"),
    "d": ("b",), "e": ("b",), "f": ("c",), "g": ("c",),
}


def vector_search():
    query = (4, 4)

    def nearest(candidates):
        def order(item):
            distance_squared = sum((point - target) ** 2 for point, target in zip(VECTORS[item], query))
            return distance_squared, item
        return sorted(candidates, key=order)[:3]

    expected = nearest(VECTORS)
    assert expected == ["d", "b", "e"]
    print("exact:", ",".join(expected))
    candidates = {"a"}
    for radius, answer in ((1, ["b", "c", "a"]), (2, expected)):
        candidates |= {neighbor for item in candidates for neighbor in EDGES[item]}
        result = nearest(candidates)
        assert result == answer
        matched = len(set(result) & set(expected))
        print(f"hops={radius}: candidates={len(candidates)}, result={','.join(result)}, recall@3={matched}/3")


@dataclass(frozen=True)
class State:
    lease_stage: int = 0  # 0 = A owns it, 1 = expired, 2 = B owns it.
    highest_accepted_token: int = 0
    visible_token: int = 0


def transitions(state, fenced):
    stage = state.lease_stage
    if stage == 0:
        yield "expire A", State(1, state.highest_accepted_token, state.visible_token)
    if stage == 1:
        yield "grant B", State(2, state.highest_accepted_token, state.visible_token)
    # A may resume after a pause with its old token. B cannot write before grant.
    available_writes = (("B writes 2", 2), ("A writes 1", 1)) if stage == 2 else (("A writes 1", 1),)
    for action, token in available_writes:
        if not fenced or token >= state.highest_accepted_token:
            yield action, State(stage, max(token, state.highest_accepted_token), token)


def examine(fenced):
    start = State()
    visited = {start}
    frontier = deque([(start, ())])
    while frontier:
        state, history = frontier.popleft()
        if state.visible_token < state.highest_accepted_token:
            return history, len(visited)
        for action, updated in transitions(state, fenced):
            if updated not in visited:
                visited.add(updated)
                frontier.append((updated, (*history, action)))
    return None, len(visited)


def lease_model():
    counterexample, _ = examine(fenced=False)
    assert counterexample == ("expire A", "grant B", "B writes 2", "A writes 1")
    print("unfenced counterexample:", " -> ".join(counterexample))
    counterexample, visited = examine(fenced=True)
    assert counterexample is None and visited == 7
    print(f"fenced: {visited} reachable states, no stale overwrite")


EXAMPLES = {"vector-search": vector_search, "lease-model": lease_model}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", choices=EXAMPLES)
    EXAMPLES[parser.parse_args().example]()
