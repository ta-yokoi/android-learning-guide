"""Compete for one item using two SQLite connections to a temporary database."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Barrier


def reserve(path, ready):
    with sqlite3.connect(path, timeout=5) as db:
        ready.wait(timeout=5)
        updated = db.execute(
            "UPDATE stock SET remaining = remaining - 1 "
            "WHERE sku = ? AND remaining >= 1",
            ("tea",),
        ).rowcount
    # Exiting the context commits the change before we report the outcome.
    return "reserved" if updated else "sold_out"


def main():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "shop.sqlite"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE stock (sku TEXT PRIMARY KEY, remaining INTEGER NOT NULL CHECK (remaining >= 0))")
            db.execute("INSERT INTO stock VALUES ('tea', 1)")
        ready = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            requests = [pool.submit(reserve, path, ready) for _ in range(2)]
            results = sorted(request.result() for request in requests)
        with sqlite3.connect(path) as db:
            remaining = db.execute("SELECT remaining FROM stock WHERE sku = 'tea'").fetchone()[0]
        assert results == ["reserved", "sold_out"] and remaining == 0
        print("outcomes:", ", ".join(results))
        print("remaining:", remaining)


if __name__ == "__main__":
    main()
