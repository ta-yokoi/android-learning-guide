"""Independent data-design experiments for Python 3.9+, standard library only."""
import argparse
from contextlib import closing
from itertools import permutations
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory


def simulate_queue(arrivals, capacity):
    finishes = []
    responses = []
    rejected = 0
    for instant in arrivals:
        finishes = [finish for finish in finishes if finish > instant]
        if len(finishes) >= capacity:
            rejected += 1
            continue
        # Serial server, 4 ms of service. Capacity includes the active request.
        finish = (finishes[-1] if finishes else instant) + 4
        finishes.append(finish)
        responses.append(finish - instant)
    return responses, rejected


def queue():
    arrivals = [0] * 8 + [32] * 4
    unbounded, accepted_all = simulate_queue(arrivals, len(arrivals))
    bounded, rejected = simulate_queue(arrivals, 3)
    assert (len(unbounded), accepted_all, max(unbounded)) == (12, 0, 32)
    assert (len(bounded), rejected, max(bounded)) == (6, 6, 12)
    slow_fanout = 1 - .99**10
    print(f"all requests: completed={len(unbounded)}, rejected={accepted_all}, max={max(unbounded)} ms")
    print(f"bounded: completed={len(bounded)}, rejected={rejected}, max={max(bounded)} ms")
    print(f"independent fan-out to 10 shards: slow probability={slow_fanout:.2%}")


def graph_sql():
    with closing(sqlite3.connect(":memory:")) as db:
        db.executescript("""
            CREATE TABLE route(src TEXT, dst TEXT, PRIMARY KEY(src, dst));
            INSERT INTO route VALUES ('A','B'), ('A','C'), ('B','C'), ('C','A'), ('C','D');
        """)
        query = """
            WITH RECURSIVE reachable(node) AS (
                VALUES (?)
                UNION
                SELECT r.dst FROM route AS r JOIN reachable AS seen ON r.src = seen.node
            )
            SELECT node FROM reachable ORDER BY node;
        """
        forward = [row[0] for row in db.execute(query, ("A",))]
        reverse = [row[0] for row in db.execute(query, ("D",))]
    assert forward == ["A", "B", "C", "D"] and reverse == ["D"]
    print("reachable from A:", ",".join(forward))
    print("reachable from D:", ",".join(reverse))


def query_plan(db, sql):
    return " | ".join(row[3] for row in db.execute("EXPLAIN QUERY PLAN " + sql))


def indexes():
    with closing(sqlite3.connect(":memory:")) as db:
        db.executescript("""
            CREATE TABLE orders(id INTEGER PRIMARY KEY, tenant INTEGER, created INTEGER,
                                amount INTEGER, details TEXT);
        """)
        db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                       ((i, i % 16, i, i * 2, "note") for i in range(8192)))
        sql = "SELECT created, amount FROM orders WHERE tenant = 7 AND created >= 7500 ORDER BY created LIMIT 4"
        without = query_plan(db, sql)
        first = db.execute(sql).fetchall()
        db.execute("CREATE INDEX orders_feed ON orders(tenant, created, amount)")
        with_index = query_plan(db, sql)
        with_details = query_plan(db, sql.replace("created, amount", "created, amount, details"))
        assert first == db.execute(sql).fetchall()
        assert "SCAN orders" in without and "TEMP B-TREE" in without
        assert "COVERING INDEX orders_feed" in with_index and "TEMP B-TREE" not in with_index
        assert "USING INDEX orders_feed" in with_details
    print("before: scan and sort")
    print("after: covering index, no sort")
    print("extra unindexed column: index plus table lookup")
    print("rows:", first)


def observed_remove():
    # An add is represented by a globally unique tag. A removal carries only
    # the tags it observed; a concurrent add therefore remains visible.
    mutations = [
        ({("A", 1)}, set()),
        (set(), {("A", 1)}),
        ({("B", 1)}, set()),
    ]
    outcomes = set()
    for delivery in permutations(mutations):
        adds, removed = set(), set()
        for step in (*delivery, delivery[0]):
            additions, tombstones = step
            adds |= additions
            removed |= tombstones
        outcomes.add(tuple(sorted(adds - removed)))
    assert outcomes == {(("B", 1),)}
    print("6 delivery orders, each with a retry: converged")
    print("visible tag after concurrent remove and add: B:1")
    # Discarding the removal record before an old peer reconnects resurrects A:1.
    assert mutations[0][0] - set() == {("A", 1)}
    print("old add with no tombstone: A:1 resurrects")


def shard_move():
    class Shard:
        def __init__(self, epoch, value, offset):
            self.epoch, self.value, self.offset = epoch, value, offset

        def write(self, epoch, value):
            if epoch != self.epoch:
                return False
            self.offset += 1
            self.value = value
            return True

    source = Shard(7, 20, 100)
    copied = Shard(None, source.value, source.offset)
    assert source.write(7, 25)
    # Freeze old writes before reading the final log boundary.
    source.epoch = None
    assert not source.write(7, 99)
    # The model has one log entry after the snapshot. Real systems replay a range.
    assert copied.offset + 1 == source.offset == 101
    copied.value, copied.offset = source.value, source.offset
    copied.epoch = 8
    assert not copied.write(7, 99) and copied.write(8, 30)
    assert copied.value == 30 and copied.offset == 102
    print("snapshot offset=100; final source offset=101")
    print("router's stale epoch 7: rejected")
    print("epoch 8 write: value=30, offset=102")


def windows():
    # A watermark starts finalization in event time. This model keeps each
    # published result correctable for a further five minutes.
    marks = [("event", "a", 2, 100), ("event", "b", 7, 200),
             ("watermark", 10), ("event", "b", 7, 200),
             ("event", "c", 8, 60), ("watermark", 15), ("event", "d", 9, 20)]
    seen, total, watermark = set(), 0, 0
    published = []
    expired = []
    for kind, *data in marks:
        if kind == "watermark":
            next_watermark = data[0]
            if watermark < 10 <= next_watermark:
                published.append((1, total))
            watermark = next_watermark
            continue
        event, minute, value = data
        assert 0 <= minute < 10  # The exercise processes the 0–10 minute window only.
        if watermark >= 15:
            expired.append(event)
        elif event not in seen:
            seen.add(event)
            total += value
            if watermark >= 10:
                published.append((len(published) + 1, total))
    assert published == [(1, 300), (2, 360)] and expired == ["d"]
    print("window versions:", published)
    print("late after retention boundary:", expired)


SOURCE_SCHEMA = """
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=FULL;
    CREATE TABLE stock(remaining INTEGER NOT NULL CHECK(remaining >= 0));
    INSERT INTO stock VALUES (2);
    CREATE TABLE orders(id TEXT PRIMARY KEY NOT NULL, amount INTEGER NOT NULL);
    CREATE TABLE outbox(seq INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL UNIQUE, amount INTEGER NOT NULL);
"""
PROJECTION_SCHEMA = """
    CREATE TABLE applied(seq INTEGER PRIMARY KEY, order_id TEXT NOT NULL UNIQUE, amount INTEGER NOT NULL);
"""


def place_order(source, order_id, amount, fail=False):
    with source:
        # Begin before reading an idempotency key so concurrent writers in this
        # one SQLite database cannot both proceed from an absent key.
        source.execute("BEGIN IMMEDIATE")
        old = source.execute("SELECT amount FROM orders WHERE id=?", (order_id,)).fetchone()
        if old is not None:
            if old[0] != amount:
                raise ValueError("same order key with different amount")
            return
        source.execute("UPDATE stock SET remaining=remaining-1")
        source.execute("INSERT INTO orders VALUES (?, ?)", (order_id, amount))
        if fail:
            raise InterruptedError("before creating the outbox event")
        source.execute("INSERT INTO outbox(order_id, amount) VALUES (?, ?)", (order_id, amount))


def read_events(source, since=0):
    return source.execute("SELECT seq, order_id, amount FROM outbox WHERE seq>? ORDER BY seq", (since,)).fetchall()


def apply(projection, rows):
    with projection:
        for seq, order_id, amount in rows:
            projection.execute("INSERT INTO applied VALUES (?, ?, ?) ON CONFLICT(seq) DO NOTHING",
                               (seq, order_id, amount))
            saved = projection.execute("SELECT order_id, amount FROM applied WHERE seq=?", (seq,)).fetchone()
            if saved != (order_id, amount):
                raise ValueError("event identity reused with different contents")


def projected_orders(projection):
    return projection.execute("SELECT order_id, amount FROM applied ORDER BY order_id").fetchall()


def capstone():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        with closing(sqlite3.connect(root / "orders.db")) as source:
            source.executescript(SOURCE_SCHEMA)
            try:
                place_order(source, "o1", 1200, fail=True)
            except InterruptedError:
                pass
            assert read_events(source) == []
            assert source.execute("SELECT remaining FROM stock").fetchone() == (2,)
            assert source.execute("SELECT COUNT(*) FROM orders").fetchone() == (0,)
            print("failure before outbox: stock=2, orders=0, events=0")

            place_order(source, "o1", 1200)
            place_order(source, "o1", 1200)
            try:
                place_order(source, "o1", 9999)
            except ValueError:
                pass
            else:
                raise AssertionError("conflicting order accepted")

            snapshot = read_events(source)
            snapshot_offset = snapshot[-1][0]
            path = root / "view.db"
            with closing(sqlite3.connect(path)) as view:
                view.executescript(PROJECTION_SCHEMA)
                apply(view, snapshot)
            # View committed, but the relay never recorded delivery. Reopen and replay.
            with closing(sqlite3.connect(path)) as view:
                apply(view, snapshot)
                assert projected_orders(view) == [("o1", 1200)]
                try:
                    apply(view, [(snapshot_offset, "o1", 9999)])
                except ValueError:
                    pass
                else:
                    raise AssertionError("inconsistent redelivery accepted")
                assert projected_orders(view) == [("o1", 1200)]
            print("lost acknowledgement and replay: 1 applied order")

            place_order(source, "o2", 800)
            with closing(sqlite3.connect(root / "rebuild.db")) as rebuilt:
                rebuilt.executescript(PROJECTION_SCHEMA)
                apply(rebuilt, snapshot)
                apply(rebuilt, read_events(source, snapshot_offset))
                expected = source.execute("SELECT id, amount FROM orders ORDER BY id").fetchall()
                actual = projected_orders(rebuilt)
                assert actual == expected == [("o1", 1200), ("o2", 800)]
                assert source.execute("SELECT remaining FROM stock").fetchone() == (0,)
                print(f"rebuilt at offset {snapshot_offset}: {len(actual)} orders, total={sum(row[1] for row in actual)}")


CASES = {
    "queue": queue, "graph-sql": graph_sql, "indexes": indexes, "observed-remove": observed_remove,
    "shard-move": shard_move, "windows": windows, "capstone": capstone,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    CASES[parser.parse_args().case]()
