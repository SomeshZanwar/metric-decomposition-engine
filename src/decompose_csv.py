import pandas as pd


def get_metric_by_dimension_from_df(df, metric_event_type, dimension_col, date_val):
    """Filter DataFrame by event_type and date, then count by dimension."""
    mask = (
        (df["event_type"] == metric_event_type) &
        (df["event_date"].astype(str) == str(date_val))
    )
    filtered = df[mask]
    if filtered.empty:
        return pd.DataFrame(columns=["dimension_value", "event_count"])
    return (
        filtered.groupby(dimension_col)
        .size()
        .reset_index(name="event_count")
        .rename(columns={dimension_col: "dimension_value"})
        .sort_values("event_count", ascending=False)
    )


def decompose_change_csv(df, metric_event_type, dimension_col, baseline_date, comparison_date):
    """Compare a metric across two dates, broken down by a dimension column."""
    baseline   = get_metric_by_dimension_from_df(df, metric_event_type, dimension_col, baseline_date)
    comparison = get_metric_by_dimension_from_df(df, metric_event_type, dimension_col, comparison_date)

    merged = pd.merge(
        baseline, comparison,
        on="dimension_value",
        how="outer",
        suffixes=("_baseline", "_comparison"),
    ).fillna(0)

    merged["segment_change"] = (
        merged["event_count_comparison"] - merged["event_count_baseline"]
    )

    total_baseline   = merged["event_count_baseline"].sum()
    total_comparison = merged["event_count_comparison"].sum()
    total_change     = total_comparison - total_baseline

    merged["contribution_pct"] = (
        (merged["segment_change"] / abs(total_change) * 100).round(2)
        if total_change != 0 else 0
    )
    merged = merged.sort_values("segment_change", key=abs, ascending=False)

    return {
        "metric":           f"Count of {metric_event_type}",
        "dimension":        dimension_col,
        "baseline_date":    str(baseline_date),
        "comparison_date":  str(comparison_date),
        "baseline_total":   int(total_baseline),
        "comparison_total": int(total_comparison),
        "total_change":     int(total_change),
        "total_change_pct": (
            round(total_change / total_baseline * 100, 2) if total_baseline > 0 else 0
        ),
        "top_contributors": merged.head(10).to_dict(orient="records"),
    }


def run_full_decomposition_csv(df, metric_event_type, baseline_date, comparison_date, dimensions):
    """Run decomposition across a list of dimension columns."""
    return {
        dim: decompose_change_csv(df, metric_event_type, dim, baseline_date, comparison_date)
        for dim in dimensions
    }