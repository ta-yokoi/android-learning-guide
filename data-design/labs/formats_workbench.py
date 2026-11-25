"""Run with Python 3.9+ and DuckDB 1.4.4 or protobuf 6.33.5, depending on the case."""
import argparse
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory


def parquet():
    import duckdb

    with TemporaryDirectory() as folder, closing(duckdb.connect()) as db:
        db.execute("SET threads = 1")
        db.execute("CREATE TABLE orders AS SELECT i AS day, i % 100 AS amount FROM range(16384) t(i)")
        for filename, order in (("ordered", "day"), ("mixed", "day % 64, day")):
            path = (Path(folder) / f"{filename}.parquet").as_posix()
            db.execute("SET VARIABLE target = ?", [path])
            # The SQL expressions come from the fixed list above.
            db.execute(f"COPY (SELECT * FROM orders ORDER BY {order}) TO (getvariable('target')) "
                       "(FORMAT PARQUET, ROW_GROUP_SIZE 2048, COMPRESSION UNCOMPRESSED)")
            groups, candidates = db.execute("""
                SELECT count(*), count(*) FILTER
                    (WHERE stats_min_value::BIGINT < 64 AND stats_max_value::BIGINT >= 0)
                FROM parquet_metadata(getvariable('target'))
                WHERE path_in_schema = 'day'
            """).fetchone()
            total = db.execute("""
                SELECT sum(amount) FROM read_parquet(getvariable('target')) WHERE day >= 0 AND day < 64
            """).fetchone()[0]
            assert groups == 8 and total == sum(range(64))
            assert candidates == (1 if filename == "ordered" else 8), (filename, candidates)
            print(f"{filename}: row groups={groups}, possible matches={candidates}, total={total}")


def protobuf():
    from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

    def message(fields):
        schema = descriptor_pb2.FileDescriptorProto(name="order.proto", package="workbench", syntax="proto3")
        order = schema.message_type.add(name="Order")
        for name, number, kind in fields:
            order.field.add(name=name, number=number, type=kind)
        pool = descriptor_pool.DescriptorPool()
        pool.Add(schema)
        return message_factory.GetMessageClass(pool.FindMessageTypeByName("workbench.Order"))

    field = descriptor_pb2.FieldDescriptorProto
    base = [("amount", 1, field.TYPE_INT32)]
    old = message(base)
    upgraded = message([*base, ("currency", 2, field.TYPE_STRING)])
    reused = message([*base, ("region", 2, field.TYPE_STRING)])

    wire = upgraded(amount=1500, currency="JPY").SerializeToString()
    relay = old.FromString(wire)
    assert relay.amount == 1500
    original = upgraded.FromString(relay.SerializeToString())
    assert original.currency == "JPY"
    fresh = upgraded.FromString(old(amount=1500).SerializeToString())
    assert fresh.currency == ""
    incorrect = reused.FromString(wire)
    assert incorrect.region == "JPY"
    print("old reader: amount=1500")
    print("binary relay preserves unknown currency:", original.currency)
    print("old writer has no currency:", repr(fresh.currency))
    print("reusing field 2 silently aliases currency as region:", incorrect.region)


CASES = {"parquet": parquet, "protobuf": protobuf}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    CASES[parser.parse_args().case]()
