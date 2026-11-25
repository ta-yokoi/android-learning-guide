"""Compare a page-based B+ tree and a sorted-run LSM model on the same trace."""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field


@dataclass
class Page:
    keys: list = field(default_factory=list)
    values: list = field(default_factory=list)
    children: list = field(default_factory=list)


class BPlusTree:
    def __init__(self, capacity=4):
        self.root = Page()
        self.capacity = capacity
        self.splits = self.probes = 0

    def put(self, key, value):
        separator = self._insert(self.root, key, value)
        if separator:
            middle, right = separator
            self.root = Page(keys=[middle], children=[self.root, right])

    def _insert(self, page, key, value):
        if page.children:
            slot = bisect_right(page.keys, key)
            split = self._insert(page.children[slot], key, value)
            if split:
                middle, right = split
                page.keys.insert(slot, middle)
                page.children.insert(slot + 1, right)
        else:
            slot = bisect_left(page.keys, key)
            if slot < len(page.keys) and page.keys[slot] == key:
                page.values[slot] = value
            else:
                page.keys.insert(slot, key)
                page.values.insert(slot, value)
        if len(page.keys) <= self.capacity:
            return None
        self.splits += 1
        mid = len(page.keys) // 2
        if page.children:
            middle = page.keys[mid]
            right = Page(keys=page.keys[mid + 1:], children=page.children[mid + 1:])
            page.keys, page.children = page.keys[:mid], page.children[:mid + 1]
            return middle, right
        right = Page(keys=page.keys[mid:], values=page.values[mid:])
        page.keys, page.values = page.keys[:mid], page.values[:mid]
        return right.keys[0], right

    def get(self, key):
        page = self.root
        while page.children:
            self.probes += 1
            page = page.children[bisect_right(page.keys, key)]
        self.probes += 1
        slot = bisect_left(page.keys, key)
        return page.values[slot] if slot < len(page.keys) and page.keys[slot] == key else None


class LSM:
    def __init__(self, capacity=4):
        self.memtable = {}
        self.runs = []
        self.capacity = capacity
        self.probes = self.flushed = self.rewritten = 0

    def put(self, key, value):
        self.memtable[key] = value
        if len(self.memtable) == self.capacity:
            self.flush()

    def flush(self):
        if self.memtable:
            entries = sorted(self.memtable.items())
            self.flushed += len(entries)
            self.runs.insert(0, tuple(zip(*entries)))
            self.memtable.clear()

    def compact(self):
        self.flush()
        latest = {}
        for keys, values in reversed(self.runs):
            latest.update(zip(keys, values))
        # None is a deletion marker. All overlapping older runs are included.
        live = sorted((key, value) for key, value in latest.items() if value is not None)
        self.rewritten += len(live)
        self.runs = [tuple(zip(*live))] if live else []

    def get(self, key):
        if key in self.memtable:
            return self.memtable[key]
        for keys, values in self.runs:
            self.probes += 1
            slot = bisect_left(keys, key)
            if slot < len(keys) and keys[slot] == key:
                return values[slot]
        return None


def main():
    tree, lsm = BPlusTree(), LSM()
    trace = [(key, 1000 + key) for key in range(16)]
    trace += [(2, 1200), (3, None), (7, 1500), (13, None)]
    truth = dict(trace)
    for key, value in trace:
        tree.put(key, value)
        lsm.put(key, value)
    lsm.flush()
    keys = sorted(set(truth) | {-1, 99})
    assert [tree.get(key) for key in keys] == [truth.get(key) for key in keys]
    assert [lsm.get(key) for key in keys] == [truth.get(key) for key in keys]
    print(f"B+ tree: splits={tree.splits}, page probes={tree.probes}")
    print(f"LSM before: runs={len(lsm.runs)}, run probes={lsm.probes}, flushed entries={lsm.flushed}")
    lsm.probes = 0
    lsm.compact()
    assert [lsm.get(key) for key in keys] == [truth.get(key) for key in keys]
    print(f"LSM after: runs={len(lsm.runs)}, run probes={lsm.probes}, rewritten entries={lsm.rewritten}")


if __name__ == "__main__":
    main()
