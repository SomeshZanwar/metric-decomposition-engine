import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


def get_metric_by_dimension(metric_event_type, dimension_col, date_val):
    """
    Count events of a given type, broken down by a dimension, for a specific date.
    """
    query = f"""
        SELECT
            {dimension_col} AS dimension_value,
            COUNT(*) AS event_count
        FROM github_events
        WHERE event_type = %(event_type)s
          AND event_date = %(date_val)s
        GROUP BY {dimension_col}
        ORDER BY event_count DESC
    """
    df = pd.read_sql(query, engine, params={
        "event_type": metric_event_type,
        "date_val": date_val,
    })
    return df


def decompose_change(metric_event_type, dimension_col, baseline_date, comparison_date):
    """
    Compare a metric across two dates, broken down by a dimension.
    Returns each segment's contribution to the total change.
    """
    baseline = get_metric_by_dimension(metric_event_type, dimension_col, baseline_date)
    comparison = get_metric_by_dimension(metric_event_type, dimension_col, comparison_date)

    # Merge on dimension value
    merged = pd.merge(
        baseline, comparison,
        on="dimension_value",
        how="outer",
        suffixes=("_baseline", "_comparison")
    ).fillna(0)

    # Calculate contribution of each segment
    merged["segment_change"] = merged["event_count_comparison"] - merged["event_count_baseline"]

    total_baseline = merged["event_count_baseline"].sum()
    total_comparison = merged["event_count_comparison"].sum()
    total_change = total_comparison - total_baseline

    merged["contribution_pct"] = (
        (merged["segment_change"] / abs(total_change) * 100).round(2)
        if total_change != 0 else 0
    )

    # Sort by absolute impact
    merged = merged.sort_values("segment_change", key=abs, ascending=False)

    summary = {
        "metric": f"Count of {metric_event_type}",
        "dimension": dimension_col,
        "baseline_date": str(baseline_date),
        "comparison_date": str(comparison_date),
        "baseline_total": int(total_baseline),
        "comparison_total": int(total_comparison),
        "total_change": int(total_change),
        "total_change_pct": round(total_change / total_baseline * 100, 2) if total_baseline > 0 else 0,
        "top_contributors": merged.head(10).to_dict(orient="records"),
    }

    return summary


def run_full_decomposition(metric_event_type, baseline_date, comparison_date):
    """
    Run decomposition across all available dimensions.
    """
    dimensions = ["actor_login", "repo_name", "org_login"]
    results = {}

    for dim in dimensions:
        print(f"Decomposing by: {dim}")
        results[dim] = decompose_change(
            metric_event_type, dim, baseline_date, comparison_date
        )

    return results


if __name__ == "__main__":
    results = run_full_decomposition(
        metric_event_type="PushEvent",
        baseline_date="2024-01-15",
        comparison_date="2024-01-22",
    )

    for dim, data in results.items():
        print(f"\n{'='*60}")
        print(f"Dimension: {data['dimension']}")
        print(f"Metric: {data['metric']}")
        print(f"Baseline ({data['baseline_date']}): {data['baseline_total']:,}")
        print(f"Comparison ({data['comparison_date']}): {data['comparison_total']:,}")
        print(f"Change: {data['total_change']:,} ({data['total_change_pct']}%)")
        print(f"\nTop 10 contributors to change:")
        for row in data["top_contributors"]:
            print(
                f"  {str(row['dimension_value']):40s} | "
                f"change: {row['segment_change']:>+8.0f} | "
                f"contribution: {row['contribution_pct']:>6.1f}%"
            )