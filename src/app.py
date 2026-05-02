import streamlit as st
import pandas as pd
from decompose import get_metric_by_dimension, decompose_change, run_full_decomposition
from report_generator import generate_report
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

st.set_page_config(page_title="Metric Decomposition Engine", layout="wide")
st.title("Metric Decomposition Engine")
st.markdown("*Automated root-cause analysis for metric changes*")

# --- Sidebar controls ---
st.sidebar.header("Configuration")

# Get available event types
event_types = pd.read_sql(
    "SELECT DISTINCT event_type FROM github_events ORDER BY event_type",
    engine
)["event_type"].tolist()

selected_event = st.sidebar.selectbox("Select Metric (Event Type)", event_types)

# Get available dates
dates = pd.read_sql(
    "SELECT DISTINCT event_date FROM github_events ORDER BY event_date",
    engine
)["event_date"].tolist()

if len(dates) < 2:
    st.error("Need at least 2 dates in the database to compare. Load more data.")
    st.stop()

baseline_date = st.sidebar.selectbox("Baseline Date", dates, index=0)
comparison_date = st.sidebar.selectbox("Comparison Date", dates, index=len(dates) - 1)

if baseline_date == comparison_date:
    st.warning("Baseline and comparison dates must be different.")
    st.stop()

dimensions = st.sidebar.multiselect(
    "Dimensions to Analyze",
    ["actor_login", "repo_name", "org_login"],
    default=["actor_login", "repo_name", "org_login"]
)

# --- Run decomposition ---
if st.sidebar.button("Run Decomposition", type="primary"):
    with st.spinner("Decomposing metric change..."):
        results = {}
        for dim in dimensions:
            results[dim] = decompose_change(
                selected_event, dim, str(baseline_date), str(comparison_date)
            )

    # Overall summary
    first = list(results.values())[0]
    direction = "increased" if first["total_change"] > 0 else "decreased"
    color = "green" if first["total_change"] > 0 else "red"

    st.markdown("---")
    st.subheader("Executive Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Baseline", f"{first['baseline_total']:,}", help=str(baseline_date))
    col2.metric("Comparison", f"{first['comparison_total']:,}", help=str(comparison_date))
    col3.metric("Change", f"{first['total_change']:+,}", f"{first['total_change_pct']}%")

    # Per-dimension results
    st.markdown("---")
    st.subheader("Dimensional Breakdown")

    for dim_name, data in results.items():
        st.markdown(f"### By `{dim_name}`")

        contributors = pd.DataFrame(data["top_contributors"])
        if contributors.empty:
            st.write("No data for this dimension.")
            continue

        contributors = contributors.rename(columns={
            "dimension_value": dim_name,
            "event_count_baseline": "Baseline Count",
            "event_count_comparison": "Comparison Count",
            "segment_change": "Change",
            "contribution_pct": "Contribution %",
        })

        # Bar chart of top 10 contributors
        chart_data = contributors.head(10).copy()
        chart_data = chart_data.set_index(dim_name)

        st.bar_chart(chart_data["Change"])
        st.dataframe(
            contributors.head(10),
            use_container_width=True,
            hide_index=True,
        )

    # Generate and display report
    st.markdown("---")
    st.subheader("Incident Report")

    report = generate_report(results)
    st.text(report)

    st.download_button(
        label="Download Report",
        data=report,
        file_name=f"incident_report_{selected_event}_{comparison_date}.txt",
        mime="text/plain",
    )