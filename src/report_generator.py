import os
import json
from datetime import datetime


def generate_report(decomposition_results):
    """
    Generate a plain-English incident report from decomposition results.
    No external API needed — uses template-based natural language.
    """
    sections = []

    # Pick the first dimension to get overall numbers
    first_dim = list(decomposition_results.values())[0]
    metric = first_dim["metric"]
    baseline_date = first_dim["baseline_date"]
    comparison_date = first_dim["comparison_date"]
    total_change = first_dim["total_change"]
    total_change_pct = first_dim["total_change_pct"]
    baseline_total = first_dim["baseline_total"]
    comparison_total = first_dim["comparison_total"]

    direction = "increased" if total_change > 0 else "decreased"

    # Header
    sections.append("=" * 70)
    sections.append("METRIC CHANGE INCIDENT REPORT")
    sections.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sections.append("=" * 70)

    # Executive summary
    sections.append("\n## EXECUTIVE SUMMARY\n")
    sections.append(
        f"{metric} {direction} by {abs(total_change_pct)}% "
        f"({baseline_total:,} → {comparison_total:,}, "
        f"change of {total_change:+,}) "
        f"between {baseline_date} and {comparison_date}."
    )

    # Dimension-by-dimension breakdown
    for dim_name, data in decomposition_results.items():
        sections.append(f"\n## BREAKDOWN BY: {dim_name.upper()}\n")

        top = data["top_contributors"][:5]

        if not top:
            sections.append("  No significant contributors found.\n")
            continue

        # Identify the single biggest driver
        biggest = top[0]
        biggest_dir = "increase" if biggest["segment_change"] > 0 else "decrease"

        sections.append(
            f"The largest contributor was '{biggest['dimension_value']}' "
            f"with a {biggest_dir} of {abs(biggest['segment_change']):,.0f} events "
            f"({abs(biggest['contribution_pct'])}% of total change)."
        )

        sections.append(f"\nTop 5 contributors:")
        for i, row in enumerate(top, 1):
            change_dir = "↑" if row["segment_change"] > 0 else "↓"
            sections.append(
                f"  {i}. {row['dimension_value']}: "
                f"{change_dir} {abs(row['segment_change']):,.0f} events "
                f"({abs(row['contribution_pct'])}% of change)"
            )

    # Root cause hypothesis
    sections.append("\n## ROOT CAUSE HYPOTHESIS\n")

    all_top_contributors = []
    for dim_name, data in decomposition_results.items():
        if data["top_contributors"]:
            top = data["top_contributors"][0]
            all_top_contributors.append({
                "dimension": dim_name,
                "value": top["dimension_value"],
                "change": top["segment_change"],
                "contribution": top["contribution_pct"],
            })

    if all_top_contributors:
        # Sort by absolute contribution
        all_top_contributors.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        primary = all_top_contributors[0]
        primary_dir = "increase" if primary["change"] > 0 else "decrease"

        sections.append(
            f"The primary driver of this metric change appears to be "
            f"'{primary['value']}' (dimension: {primary['dimension']}), "
            f"which showed a {primary_dir} of {abs(primary['change']):,.0f} events, "
            f"accounting for {abs(primary['contribution'])}% of the total change."
        )

        if len(all_top_contributors) > 1:
            secondary = all_top_contributors[1]
            secondary_dir = "increase" if secondary["change"] > 0 else "decrease"
            sections.append(
                f"\nA secondary factor is '{secondary['value']}' "
                f"(dimension: {secondary['dimension']}), contributing a "
                f"{secondary_dir} of {abs(secondary['change']):,.0f} events "
                f"({abs(secondary['contribution'])}%)."
            )

    sections.append("\n## RECOMMENDED NEXT STEPS\n")
    sections.append("  1. Investigate the top contributing segments for anomalies or known events.")
    sections.append("  2. Check if the change is sustained across multiple days or a one-time spike.")
    sections.append("  3. Cross-reference with product releases, outages, or external events on the comparison date.")
    sections.append("  4. If the change is unexpected, drill deeper into the top segment's sub-dimensions.")

    sections.append("\n" + "=" * 70)
    sections.append("END OF REPORT")
    sections.append("=" * 70)

    return "\n".join(sections)


if __name__ == "__main__":
    from decompose import run_full_decomposition

    results = run_full_decomposition(
        metric_event_type="PushEvent",
        baseline_date="2024-01-15",
        comparison_date="2024-01-22",
    )

    report = generate_report(results)
    print(report)

    # Save to file
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/incident_report_push_events.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")