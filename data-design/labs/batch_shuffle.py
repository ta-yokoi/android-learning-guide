"""Combine per-partition sales without averaging averages."""

from collections import defaultdict
from fractions import Fraction


def group(partition):
    result = defaultdict(lambda: (0, 0))
    for product, yen in partition:
        total, count = result[product]
        result[product] = total + yen, count + 1
    return result


def aggregate(partitions):
    totals = defaultdict(lambda: (0, 0))
    for partition in partitions:
        for product, (total, count) in group(partition).items():
            previous_total, previous_count = totals[product]
            totals[product] = previous_total + total, previous_count + count
    return {product: Fraction(total, count) for product, (total, count) in totals.items()}


def main():
    partitions = [[("tea", 1000)], [("tea", 400), ("tea", 600), ("tea", 800)]]
    unweighted = (1000 + 600) // 2
    average = aggregate(partitions)["tea"]
    assert unweighted == 800 and average == 700
    assert average == aggregate(reversed(partitions))["tea"]
    print("average of partition averages:", unweighted)
    print("average from total and count:", average)


if __name__ == "__main__":
    main()
