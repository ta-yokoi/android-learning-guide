"""Compare a closed-window online estimate with a batch correction."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Sale:
    event_id: str
    event_day: date
    amount_yen: int


def summarize(events, closed_day):
    canonical = {}
    online = defaultdict(int)
    duplicates = late = 0
    for event, arrival_day in events:
        previous = canonical.get(event.event_id)
        if previous is not None:
            if previous != event:
                raise ValueError("conflicting payload for event_id")
            duplicates += 1
            continue
        canonical[event.event_id] = event
        if event.event_day == closed_day and arrival_day > closed_day:
            late += 1
        else:
            online[event.event_day] += event.amount_yen
    # Rebuild the authoritative total from unique, retained events.
    corrected = sum(e.amount_yen for e in canonical.values() if e.event_day == closed_day)
    return online[closed_day], corrected, duplicates, late


def main():
    day = date(2026, 1, 10)
    next_day = date(2026, 1, 11)
    first = Sale("paid-42", day, 1200)
    late_sale = Sale("paid-43", day, 800)
    other_day = Sale("paid-44", next_day, 500)
    result = summarize([(first, day), (first, next_day),
                        (late_sale, next_day), (other_day, next_day)], day)
    assert result == (1200, 2000, 1, 1)
    online, corrected, duplicates, late = result
    print("online total:", online)
    print("corrected total:", corrected)
    print(f"duplicates: {duplicates}, late: {late}")
    try:
        summarize([(first, day), (Sale(first.event_id, day, 999), day)], day)
    except ValueError:
        print("changed event: conflict")
    else:
        raise AssertionError("conflicting event accepted")


if __name__ == "__main__":
    main()
