"""Compare on-disk SQLite and RocksDB through Python bindings.

Install rocksdict==0.3.29 for the RocksDB path. Use separate processes for
each measurement. Results are descriptive, not assertions about performance.
"""
import argparse
import hashlib
import importlib.metadata
import json
from math import ceil
from pathlib import Path
import random
import sqlite3
from tempfile import TemporaryDirectory
import time


class SQLiteEngine:
    def __init__(self, path, cache_kib):
        self.db = sqlite3.connect(path / "orders.db")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(f"PRAGMA cache_size=-{cache_kib}")
        self.db.execute("PRAGMA mmap_size=0")
        self.db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, value BLOB NOT NULL)")

    def write(self, rows):
        with self.db:
            self.db.executemany("INSERT OR REPLACE INTO orders VALUES (?,?)", rows)

    def read(self, key):
        return self.db.execute("SELECT value FROM orders WHERE id = ?", (key,)).fetchone()[0]

    def settle(self):
        self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()

    def close(self):
        self.db.close()


class RocksEngine:
    def __init__(self, path, cache_kib):
        import rocksdict as rocks

        self.rocks = rocks
        self.cache = rocks.Cache(cache_kib * 1024)
        table = rocks.BlockBasedOptions()
        table.set_block_cache(self.cache)
        table.set_cache_index_and_filter_blocks(True)
        options = rocks.Options(raw_mode=True)
        options.create_if_missing(True)
        options.set_block_based_table_factory(table)
        options.set_write_buffer_size(1024 * 1024)
        options.set_compression_type(rocks.DBCompressionType.none())
        self.db = rocks.Rdict(str(path / "rocks"), options)
        self.write_options = rocks.WriteOptions()
        self.write_options.sync = True
        self.write_options.disable_wal = False

    @staticmethod
    def key(value):
        return value.to_bytes(8, "big")

    def write(self, rows):
        batch = self.rocks.WriteBatch(raw_mode=True)
        for key, value in rows:
            batch.put(self.key(key), value)
        self.db.write(batch, self.write_options)

    def read(self, key):
        return self.db.get(self.key(key))

    def settle(self):
        self.db.flush(wait=True)

    def close(self):
        self.db.close()


def os_io():
    counters = Path("/proc/self/io")
    if not counters.is_file():
        return {}
    return {key: int(value.strip()) for key, _, value in
            (line.partition(":") for line in counters.read_text().splitlines())
            if key in ("read_bytes", "write_bytes")}


def latency(samples):
    if not samples:
        return None
    ordered = sorted(samples)
    return {f"p{int(p * 100)}_us": round(ordered[ceil(p * len(ordered)) - 1] / 1000, 2)
            for p in (.5, .95, .99)}


def measure(engine, directory, keys, batches, write_percent, seed):
    rng = random.Random(seed)
    values = [rng.randbytes(512) for _ in range(64)]
    expected = {}
    for start in range(0, keys, 32):
        rows = [(key, values[key % len(values)]) for key in range(start, min(start + 32, keys))]
        engine.write(rows)
        expected.update(rows)
    engine.settle()

    # Bound the warm-up and use the identical operation trace for both engines.
    for key in range(0, keys, 7):
        assert engine.read(key) == expected[key]
    reads, writes = [], []
    io_before = os_io()
    started = time.perf_counter_ns()
    for _ in range(batches):
        if rng.randrange(100) < write_percent:
            rows = [(rng.randrange(keys), rng.choice(values)) for _ in range(16)]
            before = time.perf_counter_ns()
            engine.write(rows)
            writes.append(time.perf_counter_ns() - before)
            expected.update(rows)
        else:
            key = rng.randrange(keys)
            before = time.perf_counter_ns()
            actual = engine.read(key)
            reads.append(time.perf_counter_ns() - before)
            assert actual == expected[key]
    seconds = (time.perf_counter_ns() - started) / 1e9
    engine.settle()
    io_after = os_io()
    size = sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())
    digest = hashlib.sha256()
    for key, value in sorted(expected.items()):
        assert engine.read(key) == value
        digest.update(value)
    return {
        "reads": len(reads), "write_batches": len(writes), "rows_per_write_batch": 16,
        "seconds_excluding_final_flush": round(seconds, 4),
        "point_read": latency(reads), "durable_batch": latency(writes),
        "file_bytes_after_flush_before_close": size,
        "process_io_bytes_including_final_flush": {key: io_after[key] - value for key, value in io_before.items()},
        "state_sha256": digest.hexdigest(),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("engine", choices=["sqlite", "rocksdb"])
    p.add_argument("--cache-kib", type=int, default=256)
    p.add_argument("--keys", type=int, default=8192)
    p.add_argument("--batches", type=int, default=1600, help="scheduled operations, either one read or a write batch")
    p.add_argument("--write-percent", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    if min(args.cache_kib, args.keys, args.batches) < 1 or not 0 <= args.write_percent <= 100:
        p.error("positive cache/keys/batches and write-percent from 0 to 100 required")
    with TemporaryDirectory(prefix="data-design-engines-") as folder:
        directory = Path(folder)
        cls = SQLiteEngine if args.engine == "sqlite" else RocksEngine
        try:
            engine = cls(directory, args.cache_kib)
        except ModuleNotFoundError as error:
            if error.name != "rocksdict":
                raise
            p.exit(2, "Install rocksdict==0.3.29 to run the RocksDB comparison.\n")
        try:
            result = measure(engine, directory, args.keys, args.batches, args.write_percent, args.seed)
        finally:
            engine.close()
    version = sqlite3.sqlite_version if args.engine == "sqlite" else importlib.metadata.version("rocksdict")
    print(json.dumps({"engine_version_or_binding": version, **vars(args), **result}, indent=2))


if __name__ == "__main__":
    main()
