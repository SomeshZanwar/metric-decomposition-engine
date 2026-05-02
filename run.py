"""
Quick entry point to run a full decomposition and generate a report.
Usage: python run.py
"""
import sys
sys.path.insert(0, "src")

from decompose import run_full_decomposition
from report_generator import generate_report


def main():
    results = run_full_decomposition(
        metric_event_type="PushEvent",
        baseline_date="2024-01-15",
        comparison_date="2024-01-22",
    )

    report = generate_report(results)
    print(report)

    with open("reports/incident_report_latest.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("\nReport saved to reports/incident_report_latest.txt")


if __name__ == "__main__":
    main()