"""Crash after applying an event and replay from the saved offset."""

import sqlite3


def apply_event(database, event_id, yen):
    with database:
        applied = database.execute(
            "INSERT INTO processed VALUES (?) ON CONFLICT(id) DO NOTHING", (event_id,)
        ).rowcount
        if applied:
            database.execute("UPDATE totals SET yen = yen + ?", (yen,))
    return bool(applied)


def main():
    database = sqlite3.connect(":memory:")
    try:
        database.executescript("""
            CREATE TABLE processed(id TEXT PRIMARY KEY);
            CREATE TABLE totals(yen INTEGER NOT NULL);
            INSERT INTO totals VALUES (0);
        """)
        # Keep the sink and simulate a consumer that restarts at the old offset.
        assert apply_event(database, "paid-42", 1200)
        first_replay = apply_event(database, "paid-42", 1200)
        assert not first_replay and apply_event(database, "paid-43", 800)
        total = database.execute("SELECT yen FROM totals").fetchone()[0]
        assert total == 2000
        print("first event applied again:", first_replay)
        print("total after replay:", total)
    finally:
        database.close()


if __name__ == "__main__":
    main()
