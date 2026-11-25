"""Runnable examples for four focused data design lessons. Python 3.9+, standard library."""
import argparse
from collections import defaultdict, deque
from contextlib import closing
from pathlib import Path
import socket
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event, Thread


def shortest_route(edges, origin, destination, max_hops):
    neighbors = defaultdict(list)
    for start, end in edges:
        neighbors[start].append(end)
    paths = deque([(origin,)])
    visited = {origin}
    while paths:
        path = paths.popleft()
        if path[-1] == destination:
            return path
        if len(path) - 1 >= max_hops:
            continue
        for neighbor in neighbors[path[-1]]:
            if neighbor not in visited:
                visited.add(neighbor)
                paths.append((*path, neighbor))
    return None


def graph():
    edges = [("A", "B"), ("A", "C"), ("B", "C"), ("C", "A"), ("C", "D")]
    at_one = shortest_route(edges, "A", "D", 1)
    at_two = shortest_route(edges, "A", "D", 2)
    assert at_one is None and at_two == ("A", "C", "D")
    assert shortest_route(edges, "D", "A", 4) is None
    print("1 hop:", at_one)
    print("2 hops:", " -> ".join(at_two))


def search():
    products = {1: ("防水 靴", 3, 4), 2: ("防水 靴", 4, 4), 3: ("靴", 1, 1)}
    postings = defaultdict(set)
    for product, (name, _, _) in products.items():
        for word in name.split():
            postings[word].add(product)
    words = postings["防水"] & postings["靴"]
    radius = 5
    rectangle = {p for p in words if all(abs(axis) <= radius for axis in products[p][1:])}
    circle = {p for p in rectangle if sum(axis**2 for axis in products[p][1:]) <= radius**2}
    assert words == rectangle == {1, 2}
    assert circle == {1}
    print("word matches:", sorted(words))
    print("rectangle:", sorted(rectangle))
    print("circle:", sorted(circle))


def order_state(connection):
    stock = connection.execute("SELECT quantity FROM stock").fetchone()[0]
    reservations = connection.execute("SELECT count(*) FROM reservations").fetchone()[0]
    return stock, reservations


def acid():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "orders.db"
        with closing(sqlite3.connect(path)) as writer, closing(sqlite3.connect(path)) as reader:
            writer.executescript("""
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=FULL;
                CREATE TABLE stock(quantity INTEGER NOT NULL CHECK(quantity >= 0));
                INSERT INTO stock VALUES (1);
                CREATE TABLE reservations(id TEXT PRIMARY KEY NOT NULL);
            """)
            try:
                with writer:
                    writer.execute("UPDATE stock SET quantity = quantity - 1")
                    raise InterruptedError("before inserting the reservation")
            except InterruptedError:
                pass
            after_abort = order_state(reader)
            assert after_abort == (1, 0)
            print("after rollback:", after_abort)

            with writer:
                writer.execute("UPDATE stock SET quantity = quantity - 1")
                writer.execute("INSERT INTO reservations VALUES ('order-42')")
                before_commit = order_state(reader)
                assert before_commit == (1, 0)
                print("before commit, other connection:", before_commit)

            invalid_changes = (
                "UPDATE stock SET quantity = quantity - 1",
                "INSERT INTO reservations VALUES ('order-42')",
            )
            for sql in invalid_changes:
                try:
                    with writer:
                        writer.execute(sql)
                except sqlite3.IntegrityError:
                    continue
                raise AssertionError("invalid order state accepted")
            print("constraints: negative stock and duplicate ID rejected")

        with closing(sqlite3.connect(path)) as reopened:
            final = order_state(reopened)
            assert final == (0, 1)
            print("after reopen:", final)


def reservation_exchange(mode, reservations):
    # The loopback peer handles just one request. Events let the test hold the
    # response past the deadline without relying on a fixed server sleep.
    committed, allow_reply = Event(), Event()
    errors = []
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(3)

        def accept_one():
            try:
                connection, _ = listener.accept()
                with connection, connection.makefile("rb") as request:
                    connection.settimeout(3)
                    key = request.readline(64).strip()
                    if not key:
                        return
                    response = reservations.setdefault(key, b"reserved")
                    committed.set()
                    if mode == "closed":
                        return
                    if mode == "held":
                        assert allow_reply.wait(3)
                        return
                    connection.sendall(response)
            except (OSError, AssertionError) as error:
                errors.append(error)

        peer = Thread(target=accept_one)
        peer.start()
        try:
            with socket.create_connection(listener.getsockname(), timeout=3) as client:
                if mode == "unsent":
                    return None
                client.sendall(b"order-42:reserve\n")
                if mode == "held":
                    assert committed.wait(3)
                    client.settimeout(0.1)
                try:
                    data = client.recv(64)
                except socket.timeout:
                    return "deadline"
                return "closed" if not data else data.decode()
        finally:
            allow_reply.set()
            peer.join()
            if errors:
                raise errors[0]


def network():
    for mode, expected, count in (("unsent", None, 0), ("held", "deadline", 1), ("closed", "closed", 1)):
        reservations = {}
        outcome = reservation_exchange(mode, reservations)
        assert outcome == expected and len(reservations) == count
        print(f"{mode}: client={outcome or 'no reply'}; reservations={count}")
        assert reservation_exchange("normal", reservations) == "reserved"
        assert len(reservations) == 1
    print("retry with same key: exactly one reservation in all scenarios")


EXAMPLES = {"graph": graph, "search": search, "acid": acid, "network": network}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", choices=EXAMPLES)
    EXAMPLES[parser.parse_args().example]()
