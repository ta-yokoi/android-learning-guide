"""Deterministic model of Raft log replication and crash recovery.

Models persistent term/vote/log, RequestVote, AppendEntries, and the
current-term commit rule. Timeouts, real networking and disks are abstracted.
"""
import argparse
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entry:
    term: int
    command: str


@dataclass(frozen=True)
class Snapshot:
    index: int
    term: int
    state: tuple


@dataclass
class Disk:
    term: int = 0
    vote: str = ""
    log: list = field(default_factory=lambda: [Entry(0, "sentinel")])
    snapshot: Snapshot = field(default_factory=lambda: Snapshot(0, 0, ()))

    def last(self):
        return self.log[-1].term, self.snapshot.index + len(self.log) - 1

    def term_at(self, index):
        offset = index - self.snapshot.index
        return self.log[offset].term if 0 <= offset < len(self.log) else None

    def suffix(self, start):
        return self.log[start - self.snapshot.index:]


@dataclass
class Node:
    name: str
    disk: Disk
    commit_index: int = 0

    def __post_init__(self):
        self.commit_index = max(self.commit_index, self.disk.snapshot.index)

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
        own_term = self.disk.term_at(previous)
        if own_term is None or own_term != prior_term:
            return False
        start = previous + 1 - self.disk.snapshot.index
        for index, entry in enumerate(entries, start):
            if index == len(log):
                log.extend(entries[index - start:])
                break
            if log[index].term != entry.term:
                assert index + self.disk.snapshot.index > self.commit_index
                log[index:] = entries[index - start:]
                break
            assert log[index] == entry
        self.commit_index = max(self.commit_index, min(leader_commit, previous + len(entries)))
        return True

    def applied(self):
        return list(self.state_through(self.commit_index))

    def state_through(self, index):
        end = index - self.disk.snapshot.index + 1
        commands = (entry.command for entry in self.disk.log[1:end] if entry.command != "noop")
        return self.disk.snapshot.state + tuple(commands)

    def compact(self, index):
        assert self.disk.snapshot.index < index <= self.commit_index
        snap = Snapshot(index, self.disk.term_at(index), self.state_through(index))
        self.install_snapshot(self.disk.term, snap, local=True)
        return snap

    def install_snapshot(self, term, snapshot, *, local=False):
        self.advance_term(term)
        if term < self.disk.term:
            return False
        if snapshot.index <= self.disk.snapshot.index or (not local and snapshot.index <= self.commit_index):
            return True
        tail = self.disk.suffix(snapshot.index + 1) if self.disk.term_at(snapshot.index) == snapshot.term else []
        # This state update represents a single durable replacement in the model.
        self.disk.snapshot = snapshot
        self.disk.log = [Entry(snapshot.term, "sentinel"), *tail]
        self.commit_index = max(self.commit_index, snapshot.index)
        return True


def elect(candidate, term, reachable):
    assert candidate in reachable
    grants = sum(peer.request_vote(term, candidate.name, candidate.disk.last()) for peer in reachable)
    return grants >= 2  # The configured cluster always contains three voters.


def replicate(leader, follower, next_index):
    disk = leader.disk
    rejected = 0
    while next_index >= 1:
        if next_index <= disk.snapshot.index:
            if not follower.install_snapshot(disk.term, disk.snapshot):
                return None, rejected
            next_index = disk.snapshot.index + 1
        previous = next_index - 1
        if follower.append_entries(disk.term, previous, disk.term_at(previous),
                                   disk.suffix(next_index), leader.commit_index):
            return disk.last()[1], rejected
        if follower.disk.term > leader.disk.term:
            return None, rejected + 1
        boundary = follower.disk.snapshot
        if boundary.index > previous:
            assert disk.term_at(boundary.index) == boundary.term, "follower snapshot conflicts with leader"
            next_index = boundary.index + 1
        else:
            next_index -= 1
        rejected += 1
    raise AssertionError("missing sentinel")


def try_commit(leader, confirmed, index):
    if sum(position >= index for position in confirmed) >= 2 and leader.disk.term_at(index) == leader.disk.term:
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


def partition_scenarios():
    a, b, c = [Node(name, Disk()) for name in "ABC"]
    assert elect(a, 1, [a, b, c])
    a.disk.log.append(Entry(1, "isolated-A"))
    assert not try_commit(a, [1, 0, 0], 1)
    assert not elect(c, 2, [c])
    print("quorum lost: no election or commit")

    assert elect(b, 3, [b, c])
    b.disk.log.append(Entry(3, "order-42"))
    matched, _ = replicate(b, c, 1)
    assert try_commit(b, [1, matched], 1)
    replicate(b, c, 2)

    # B now loses contact. C has the committed entry; stale A can join C.
    assert not elect(a, 4, [a, c])
    assert elect(c, 5, [a, c])
    c.disk.log.append(Entry(5, "order-43"))
    matched, rejected = replicate(c, a, 2)
    assert rejected == 1 and try_commit(c, [2, matched], 2)
    replicate(c, a, 3)
    assert a.applied() == c.applied() == ["order-42", "order-43"]
    assert not a.append_entries(3, 1, 3, [Entry(3, "stale")], 1)
    print("second partition: stale log resisted; term 5 committed", c.applied())

    snapshot = c.compact(2)
    assert snapshot == Snapshot(2, 5, ("order-42", "order-43"))
    c.disk.log.append(Entry(5, "order-44"))
    matched, _ = replicate(c, a, 3)
    assert try_commit(c, [3, matched], 3)

    recovered = Node("B", b.disk)
    _, rejected = replicate(c, recovered, 4)
    assert rejected == 2 and recovered.disk.snapshot == snapshot
    assert recovered.applied() == c.applied() == ["order-42", "order-43", "order-44"]
    print("snapshot installed at:", recovered.disk.snapshot.index)
    print("state after replay:", recovered.applied())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partitions", action="store_true", help="run partition and snapshot scenarios")
    if parser.parse_args().partitions:
        partition_scenarios()
    else:
        main()
