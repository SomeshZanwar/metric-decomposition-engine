import os
import sys
import streamlit as st
import pandas as pd

sys.path.insert(0, "src")
from decompose_csv import run_full_decomposition_csv
from report_generator import generate_report

st.set_page_config(
    page_title="Metric Change Investigator",
    page_icon="🔍",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔍 Metric Change Investigator")
st.markdown(
    "**Find what drove a KPI movement across segments — in seconds.**  \n"
    "Answers the question every analytics team gets on Monday morning: "
    "*Why did this metric drop?*"
)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")

    data_source = st.radio("Data Source", ["📦 Sample dataset", "📤 Upload CSV"])
    df = None

    if data_source == "📦 Sample dataset":
        csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "sample_data",
            "github_events_sample.csv",
        )
        try:
            df = pd.read_csv(csv_path)
            st.success("✓ Sample data loaded")
            with st.expander("About this dataset"):
                st.caption(
                    "GitHub Archive events (PushEvent, PullRequestEvent, IssuesEvent) "
                    "across Jan 15 and Jan 22, 2024. PushEvents dropped ~55% — "
                    "this tool will show you which actors and repos drove it."
                )
        except FileNotFoundError:
            st.error(
                "Sample file not found. "
                "Run: `python sample_data/generate_sample.py`"
            )
            st.stop()

    else:
        st.markdown(
            "**Required columns:** `event_date`, `event_type` + at least one "
            "dimension column  \n"
            "Example: `actor_login`, `repo_name`, `org_login`"
        )
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded is None:
            st.info("Waiting for file...")
            st.stop()
        df = pd.read_csv(uploaded)

    # Validate
    if df is not None:
        required = {"event_date", "event_type"}
        if not required.issubset(df.columns):
            st.error(f"CSV must contain: {required}. Found: {set(df.columns)}")
            st.stop()

        df["event_date"] = df["event_date"].astype(str)

        event_types = sorted(df["event_type"].dropna().unique())
        selected_event = st.selectbox("Metric (Event Type)", event_types)

        dates = sorted(df["event_date"].dropna().unique())
        if len(dates) < 2:
            st.error("Need at least 2 distinct dates.")
            st.stop()

        baseline_date   = st.selectbox("Baseline Date (earlier)", dates, index=0)
        comparison_date = st.selectbox("Comparison Date (later)", dates, index=len(dates) - 1)

        if baseline_date == comparison_date:
            st.warning("Select different dates.")
            st.stop()

        non_dim = {"event_id", "event_type", "created_at", "event_date"}
        avail_dims = [c for c in df.columns if c not in non_dim]

        selected_dims = st.multiselect(
            "Dimensions to Analyze",
            avail_dims,
            default=avail_dims[:3] if len(avail_dims) >= 3 else avail_dims,
        )

        run_btn = st.button("🔍 Run Decomposition", type="primary", use_container_width=True)

# ── Landing state ─────────────────────────────────────────────────────────────
if df is None or not run_btn:
    st.markdown(
        """
        ### How it works
        1. Load sample data or upload your own CSV
        2. Select a metric, two time periods, and which dimensions to analyze
        3. Click **Run Decomposition**
        4. The engine ranks every segment by its contribution to the total change
        5. Download a stakeholder-ready incident report

        ### What this replaces
        The standard analyst workflow for metric investigations is:
        manually slicing data by dimension after dimension in SQL,
        trying to find where the change came from.
        This tool does all of that automatically and ranks the results.

        ### Expected CSV format
        ```
        event_date,event_type,actor_login,repo_name,org_login
        2024-01-15,PushEvent,alice-dev,alice-dev/project-01,tech-corp
        2024-01-22,PushEvent,alice-dev,alice-dev/project-01,tech-corp
        ...
        ```
        """
    )
    st.stop()

if not selected_dims:
    st.warning("Select at least one dimension.")
    st.stop()

# ── Run decomposition ─────────────────────────────────────────────────────────
with st.spinner("Decomposing metric change..."):
    results = run_full_decomposition_csv(
        df, selected_event, baseline_date, comparison_date, selected_dims
    )

first     = list(results.values())[0]
total_chg = first["total_change"]
chg_pct   = first["total_change_pct"]

st.subheader("Executive Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Baseline",   f"{first['baseline_total']:,}",   help=baseline_date)
c2.metric("Comparison", f"{first['comparison_total']:,}", help=comparison_date)
c3.metric("Change",     f"{total_chg:+,}",                f"{chg_pct:+.1f}%")

direction = "increased" if total_chg > 0 else "decreased"
st.markdown(
    f"**{first['metric']}** {direction} by **{abs(chg_pct):.1f}%** "
    f"between `{baseline_date}` and `{comparison_date}`."
)
st.divider()

st.subheader("Dimensional Breakdown")
for dim_name, data in results.items():
    st.markdown(f"#### By `{dim_name}`")
    contrib_df = pd.DataFrame(data["top_contributors"])
    if contrib_df.empty:
        st.caption("No data for this dimension.")
        continue

    contrib_df = contrib_df.rename(columns={
        "dimension_value":        dim_name,
        "event_count_baseline":   "Baseline",
        "event_count_comparison": "Comparison",
        "segment_change":         "Change",
        "contribution_pct":       "Contribution %",
    })

    st.bar_chart(contrib_df.head(10).set_index(dim_name)[["Change"]])
    st.dataframe(contrib_df.head(10), use_container_width=True, hide_index=True)

st.divider()
st.subheader("📄 Incident Report")
report = generate_report(results)
st.text(report)

st.download_button(
    "⬇️ Download Report (.txt)",
    data=report,
    file_name=f"incident_report_{selected_event}_{comparison_date}.txt",
    mime="text/plain",
    use_container_width=True,
)