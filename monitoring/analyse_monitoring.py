#!/usr/bin/env python3
"""Summarise manually recorded Cisco Packet Tracer test results from a CSV.

Usage (from this folder):
    python analyse_monitoring.py

This script analyses recorded observations only. It does not collect live
traffic or independently prove which device caused a failed connection.
"""
import csv
import sys
from pathlib import Path

DEFAULT_CSV = Path(__file__).with_name("monitoring-log.csv")
REQUIRED_FIELDS = [
    "timestamp", "device", "monitor_type", "test_name",
    "source", "destination", "expected_result", "actual_result",
]


def classify(row):
    expected = (row.get("expected_result") or "").strip().upper()
    actual = (row.get("actual_result") or "").strip().upper()

    if not expected or not actual:
        return "INVESTIGATE", "Expected or actual result is missing."

    if expected == actual:
        return "PASS", f"Recorded result matches expectation ({actual})."

    # A ping timeout is consistent with a blocked ping, but by itself does
    # not prove that the firewall caused the timeout.
    if expected == "PING_BLOCKED" and actual in {"PING_TIMEOUT", "NO_REPLY", "BLOCKED"}:
        return "INVESTIGATE", (
            "Ping timed out as expected; verify ASA ACL counters before "
            "attributing the block to the firewall."
        )

    return "INVESTIGATE", f"Recorded result ({actual}) differs from expectation ({expected})."


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not path.exists():
        print(f"ERROR: CSV file not found: {path}")
        raise SystemExit(1)

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = [field for field in REQUIRED_FIELDS if field not in headers]
        if missing:
            print("ERROR: Missing required CSV columns: " + ", ".join(missing))
            print("Found columns: " + ", ".join(headers))
            raise SystemExit(1)
        rows = list(reader)

    print(f"Monitoring report: {path}")
    print("=" * 72)
    if not rows:
        print("No observations found. Add test results to the CSV first.")
        return

    counts = {"PASS": 0, "INVESTIGATE": 0, "ALERT": 0}
    for row in rows:
        test_name = (row.get("test_name") or "Unnamed test").strip()
        status, explanation = classify(row)
        counts[status] += 1
        source = (row.get("source") or "?").strip()
        destination = (row.get("destination") or "?").strip()
        print(f"[{status}] {test_name}")
        print(f"  Device: {row.get('device', '').strip()} | Type: {row.get('monitor_type', '').strip()}")
        print(f"  Path: {source} -> {destination}")
        print(f"  Expected: {row.get('expected_result', '').strip()} | Actual: {row.get('actual_result', '').strip()}")
        print(f"  Note: {explanation}")

    print("=" * 72)
    print("Summary:")
    for status, count in counts.items():
        print(f"  {status}: {count}")
    print("\nLimitations: this report summarises manually entered CSV results only. "
          "It does not capture live traffic or independently verify firewall behaviour.")


if __name__ == "__main__":
    main()
