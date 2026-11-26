"""Check real PostgreSQL isolation in an ephemeral local server on Linux or macOS."""
from pathlib import Path
from tempfile import TemporaryDirectory

import pgserver
import psycopg
from psycopg import errors


def refresh_view(uri, isolation):
    with psycopg.connect(uri, autocommit=True) as writer, psycopg.connect(uri, autocommit=True) as reader:
        writer.execute("TRUNCATE reservations")
        writer.execute("INSERT INTO reservations VALUES (1)")
        with reader.transaction():
            reader.execute("SET TRANSACTION ISOLATION LEVEL " + isolation)
            before = reader.execute("SELECT count(*) FROM reservations").fetchone()[0]
            writer.execute("INSERT INTO reservations VALUES (2)")
            after = reader.execute("SELECT count(*) FROM reservations").fetchone()[0]
    return before, after


def take_leave(uri, isolation):
    with psycopg.connect(uri, autocommit=True) as setup, psycopg.connect(uri) as a, psycopg.connect(uri) as b:
        setup.execute("UPDATE duty SET on_duty = true")
        for transaction in (a, b):
            transaction.execute("SET TRANSACTION ISOLATION LEVEL " + isolation)
            assert transaction.execute("SELECT count(*) FROM duty WHERE on_duty").fetchone() == (2,)
        commits, retries = 0, 0
        # The two readers already have their snapshots. Update different rows.
        for transaction, name in ((a, "A"), (b, "B")):
            try:
                transaction.execute("UPDATE duty SET on_duty=false WHERE worker=%s", (name,))
                transaction.commit()
                commits += 1
            except errors.SerializationFailure as failure:
                assert failure.sqlstate == "40001"
                transaction.rollback()
                retries += 1
        remaining = setup.execute("SELECT count(*) FROM duty WHERE on_duty").fetchone()[0]
        return commits, retries, remaining


def main():
    with TemporaryDirectory(prefix="data-design-pg-") as directory:
        with pgserver.get_server(Path(directory) / "cluster", cleanup_mode="delete") as server:
            uri = server.get_uri()
            with psycopg.connect(uri, autocommit=True) as db:
                db.execute("CREATE TABLE reservations(id INTEGER PRIMARY KEY)")
                db.execute("CREATE TABLE duty(worker TEXT PRIMARY KEY, on_duty BOOLEAN NOT NULL)")
                db.execute("INSERT INTO duty VALUES ('A', true), ('B', true)")
            for isolation, expected in (("READ COMMITTED", (1, 2)), ("REPEATABLE READ", (1, 1))):
                before, after = refresh_view(uri, isolation)
                assert (before, after) == expected
                print(f"{isolation}: reservations {before} -> {after}")
            for isolation, expected in (("REPEATABLE READ", (2, 0, 0)), ("SERIALIZABLE", (1, 1, 1))):
                commits, retries, remaining = take_leave(uri, isolation)
                assert (commits, retries, remaining) == expected
                print(f"{isolation}: commits={commits}, retry_40001={retries}, on_duty={remaining}")


if __name__ == "__main__":
    main()
