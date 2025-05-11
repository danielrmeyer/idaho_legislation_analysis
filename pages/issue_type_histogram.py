# pages/issue_type_histogram.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pathlib import Path

from utils import load_data

# @st.cache_data
# def load_data():
#     run = os.getenv("DATARUN")
#     if not run:
#         st.error("Please set DATARUN in your environment.")
#         st.stop()
#     path = Path("Data") / f"idaho_bills_enriched_{run}.jsonl"
#     df = pd.read_json(path, orient="records", lines=True)
#     return df

df = load_data()

st.title("Distribution of Constitutional Issue Types")

# Flatten and count
all_issues = [
    issue.get("issue")
    for issues in df["json_data"]
    if isinstance(issues, list)
    for issue in issues
    if issue.get("issue")
]
if not all_issues:
    st.info("No issues data to plot.")
    st.stop()

issue_counts = (
    pd.Series(all_issues)
    .value_counts()
    .reset_index()
    .rename(columns={"index": "issue_type", 0: "count"})
)

# Let user choose how many to display
max_n = len(issue_counts)
top_n = st.slider(
    "Show top N issue types", min_value=5, max_value=min(50, max_n), value=20
)

top_counts = issue_counts.head(top_n)

# Horizontal bar chart
fig = px.bar(
    top_counts,
    x="count",
    y="issue_type",
    orientation="h",
    title=f"Top {top_n} Issue Types by Frequency",
    labels={"count": "Number of Occurrences", "issue_type": "Issue Type"},
)

# Tweak layout: enough left margin for labels, dynamic height
fig.update_layout(
    margin={"l": 200, "r": 20, "t": 60, "b": 20},
    height=30 * top_n + 200,
)

st.plotly_chart(fig, use_container_width=True)
