"""Model newest-first lookup across two sorted-run representations."""

DELETED = object()
MISSING = object()


def lookup(key, runs):
    for run in runs:
        if key in run:
            return MISSING if run[key] is DELETED else run[key]
    return MISSING


def compact_all(runs):
    merged = {}
    for run in reversed(runs):
        merged.update(run)
    # Safe here because all overlapping older runs are included.
    return {key: value for key, value in merged.items() if value is not DELETED}


def main():
    older = {"tea": 1000, "cup": 300}
    newer = {"tea": 1200, "cup": DELETED}
    before = [newer, older]
    after = [compact_all(before)]
    assert lookup("tea", before) == lookup("tea", after) == 1200
    assert lookup("cup", before) is lookup("cup", after) is MISSING
    unsafe = [{key: value for key, value in newer.items() if value is not DELETED}, older]
    assert lookup("cup", unsafe) == 300
    print("latest tea:", lookup("tea", after))
    print("cup after full compaction: absent")
    print("cup after dropping only the marker:", lookup("cup", unsafe))


if __name__ == "__main__":
    main()
