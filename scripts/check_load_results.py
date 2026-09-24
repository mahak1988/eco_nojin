#!/usr/bin/env python3
"""Check load test results from Locust CSV output."""

import csv
import sys

with open("load_results_stats.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["Name"] == "Aggregated":
            p95 = float(row["95%"])
            p99 = float(row["99%"])
            failures = (
                float(row["Failure Count"]) / float(row["Request Count"]) * 100
                if float(row["Request Count"]) > 0
                else 0
            )
            print(f"P95: {p95:.0f}ms, P99: {p99:.0f}ms, Failure rate: {failures:.1f}%")
            if p99 > 200:
                print(f"::error::P99 latency {p99:.0f}ms exceeds 200ms threshold")
                sys.exit(1)
            if failures > 5:
                print(f"::error::Failure rate {failures:.1f}% exceeds 5% threshold")
                sys.exit(1)
            print("Load test passed!")
            sys.exit(0)

print("Could not find Aggregated row in results")
sys.exit(1)
