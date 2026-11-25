"""Deterministic model of Raft log replication and crash recovery.

Models persistent term/vote/log, RequestVote, AppendEntries, and the
current-term commit rule. Timeouts, real networking and disks are abstracted.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entry:
    term: int
    command: str


@dataclass
class Disk:
    term: int = 0
    vote: str = ""
    log: list = field(default_factory=lambda: [Entry(0, "sentinel")])

    def last(self):
        return self.log[-1].term, len(self.log) - 1


@dataclass
class Node:
    name: str
    disk: Disk
    commit_index: int = 0

    def advance_term(self, term):
        if term > self.disk.term:
            self.disk.term, self.disk.vote = term, ""

    def request_vote(self, term, candidate, last):
        self.advance_term(term)
        if term < self.disk.term or last < self.disk.last():
            return False
        if self.disk.vote and self.disk.vote != candidate:
            return False
        self.disk.vote = candidate
        return True

    def append_entries(self, term, previous, prior_term, entries, leader_commit):
        self.advance_term(term)
        if term < self.disk.term:
            return False
        log = self.disk.log
        if previous >= len(log) or log[previous].term != prior_term:
            return False
        for index, entry in enumerate(entries, previous + 1):
            if index == len(log):
                log.extend(entries[index - previous - 1:])
                break
            if log[index].term != entry.term:
                assert index > self.commit_index
                log[index:] = entries[index - previous - 1:]
                break
            assert log[index] == entry
        self.commit_index = max(self.commit_index, min(leader_commit, previous + len(entries)))
        return True

    def applied(self):
        return [e.command for e in self.disk.log[1:self.commit_index + 1] if e.command != "noop"]


def elect(candidate, term, reachable):
    assert candidate in reachable
    grants = sum(peer.request_vote(term, candidate.name, candidate.disk.last()) for peer in reachable)
    return grants >= 2  # The configured cluster always contains three voters.


def replicate(leader, follower, next_index):
    log = leader.disk.log
    rejected = 0
    while next_index >= 1:
        previous = next_index - 1
        if follower.append_entries(leader.disk.term, previous, log[previous].term,
                                   log[next_index:], leader.commit_index):
            return len(log) - 1, rejected
        if follower.disk.term > leader.disk.term:
            return None, rejected + 1
        next_index -= 1
        rejected += 1
    raise AssertionError("missing sentinel")


def try_commit(leader, confirmed, index):
    if sum(position >= index for position in confirmed) >= 2 and leader.disk.log[index].term == leader.disk.term:
        leader.commit_index = max(leader.commit_index, index)
        return True
    return False


def main():
    a, b, c = [Node(name, Disk()) for name in "ABC"]
    assert elect(a, 1, [a, b, c])
    a.disk.log.append(Entry(1, "order-42"))
    copied, _ = replicate(a, b, 1)
    assert try_commit(a, [1, copied], 1)
    replicate(a, b, 2)  # B learns the commit via a heartbeat.
    a.disk.log.append(Entry(1, "unconfirmed-99"))
    assert not try_commit(a, [2, 1, 0], 2)
    print("old leader committed:", a.applied())

    # A becomes unreachable. B's up-to-date log allows election with C.
    assert elect(b, 2, [b, c])
    copied, _ = replicate(b, c, 2)
    assert not try_commit(b, [1, copied], 1)  # This entry belongs to term 1.
    b.disk.log.append(Entry(2, "noop"))
    copied, _ = replicate(b, c, 2)
    assert try_commit(b, [2, copied], 2)
    b.disk.log.append(Entry(2, "order-43"))
    copied, _ = replicate(b, c, 3)
    assert try_commit(b, [3, copied], 3)
    print("new leader committed:", b.applied())

    # A restarts with its persisted log, but has lost volatile commit_index.
    restarted = Node("A", a.disk)
    _, rejected = replicate(b, restarted, 4)
    replicate(b, c, 4)
    assert rejected == 2 and restarted.disk.log == b.disk.log == c.disk.log
    assert restarted.applied() == b.applied() == c.applied() == ["order-42", "order-43"]
    print("recovery prefix rejections:", rejected)
    print("recovered state:", restarted.applied())


if __name__ == "__main__":
    main()
