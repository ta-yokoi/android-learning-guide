"""Exercise old and new JSON readers, including a type-breaking change."""
import json


def read_v1(payload):
    event = json.loads(payload)
    if not isinstance(event["warehouse"], str):
        raise ValueError("warehouse must be a string")
    return event["warehouse"]


def read_v2(payload):
    event = json.loads(payload)
    legacy = read_v1(payload)
    warehouses = event.get("warehouses", [legacy])
    if not isinstance(warehouses, list) or not all(isinstance(code, str) for code in warehouses):
        raise ValueError("warehouses must be a list of strings")
    return warehouses


def main():
    old = '{"warehouse":"W01"}'
    additive = '{"warehouse":"W01","warehouses":["W01","W02"]}'
    breaking = '{"warehouse":["W01","W02"]}'
    old_to_new = read_v2(old)
    new_to_old = read_v1(additive)
    assert old_to_new == ["W01"] and new_to_old == "W01"
    assert read_v2(additive) == ["W01", "W02"]
    print("old data read by v2:", old_to_new)
    print("new data read by v1:", new_to_old)
    try:
        read_v1(breaking)
    except ValueError as error:
        print("in-place type change:", error)
    else:
        raise AssertionError("v1 accepted an incompatible type")


if __name__ == "__main__":
    main()
