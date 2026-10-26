#!/usr/bin/env python3
"""Analyse manually recorded Packet Tracer monitoring observations.

Usage:
    python monitoring/analyse_monitoring.py
    python monitoring/analyse_monitoring.py monitoring/monitoring-log.csv

This script analyses CSV data only. It does not collect live data from Packet Tracer.
"""
import csv
import sys
from pathlib import Path

DEFAULT_CSV = Path(__file__).with_name("monitoring-log.csv")
FIELDS = [
    "timestamp", "device", "monitor_type", "test_name", "source", "destination",
    "expected_result", "actual_result", "acl_hit_count_before", "acl_hit_count_after",
    "port_security_violations_before", "port_security_violations_after",
    "status", "evidence", "notes",
]

def number(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not path.exists():
        print(f"ERROR: CSV file not found: {path}")
        raise SystemExit(1)

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            print("ERROR: Missing required CSV columns: " + ", ".join(missing))
            raise SystemExit(1)
        rows = list(reader)

    if not rows:
        print("No observations found. Add actual test results to the CSV first.")
        return

    counts = {"PASS": 0, "INVESTIGATE": 0, "ALERT": 0, "UNCLASSIFIED": 0}
    print(f"Monitoring report: {path}")
    print("=" * 72)

    for index, row in enumerate(rows, start=2):
        if row.get("test_name", "").strip() == "EXAMPLE-REPLACE-ME":
            print(f"Row {index}: placeholder row — replace with real observations.")
            continue

        status = (row.get("status") or "").strip().upper()
        before = number(row.get("port_security_violations_before"))
        after = number(row.get("port_security_violations_after"))
        actual = (row.get("actual_result") or "").strip()
        expected = (row.get("expected_result") or "").strip()
        reasons = []

        if status not in counts or status == "UNCLASSIFIED":
            status = "UNCLASSIFIED"
        if actual and expected and actual.casefold() != expected.casefold():
            reasons.append("actual result differs from expected result")
            if status == "PASS":
                status = "INVESTIGATE"
        if before is not None and after is not None and after > before:
            reasons.append(f"port-security violation count increased ({before} -> {after})")
            status = "ALERT"
        if not actual or actual.upper() == "NOT_TESTED":
            reasons.append("actual result not recorded")
            if status == "PASS":
                status = "INVESTIGATE"

        counts[status] += 1
        label = row.get("test_name") or f"row {index}"
        print(f"[{status}] {label}")
        for reason in reasons:
            print(f"  - {reason}")
        if not reasons:
            print(f"  - Recorded outcome: {actual or 'not provided'}")

    print("=" * 72)
    print("Summary:")
    for key, value in counts.items():
        print(f"  {key}: {value}")
    print("\nReminder: review the original CLI/browser evidence. This report evaluates recorded CSV values; it does not independently verify network behaviour.")

if __name__ == "__main__":
    main()
