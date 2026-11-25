"""Exercise majority intersection and a simplified Raft voting rule."""
from dataclasses import dataclass
from itertools import combinations


@dataclass
class Voter:
    term: int
    last_log: tuple  # (last log term, last log index)
    choice: str = ""

    def vote(self, term, candidate, last_log):
        if term < self.term:
            return False
        if term > self.term:
            self.term, self.choice = term, ""
        if last_log < self.last_log or self.choice not in ("", candidate):
            return False
        self.choice = candidate
        return True


def main():
    pairs = [set(pair) for pair in combinations("ABC", 2)]
    minimum_overlap = min(len(a & b) for a in pairs for b in pairs)
    voters = {name: Voter(1, (1, 5)) for name in "ABC"}
    first = sum(voters[name].vote(2, "A", (1, 5)) for name in "AB")
    competing = sum(voters[name].vote(2, "C", (1, 5)) for name in "BC")
    stale_log = sum(v.vote(3, "C", (1, 4)) for v in voters.values())
    assert (minimum_overlap, first, competing, stale_log) == (1, 2, 1, 0)
    print("minimum majority overlap:", minimum_overlap)
    print("votes for first candidate:", first)
    print("votes for competing candidate:", competing)
    print("votes for stale log:", stale_log)


if __name__ == "__main__":
    main()
