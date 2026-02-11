"""Histogram showing total constitutional issues grouped by bill sponsor."""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data

# Load and prepare
df = load_data()

st.title("Constitutional Issues by Sponsor")

# Compute total issues per sponsor
# df.issue_count counts per bill; sum across bills grouped by sponsor
issues_by_sponsor = (
    df.groupby("sponsor")["issue_count"]
    .sum()
    .reset_index()
    .rename(columns={"issue_count": "total_issues"})
    .sort_values("total_issues", ascending=False)
)

if issues_by_sponsor["total_issues"].sum() == 0:
    st.info("No issues detected for any sponsor.")
    st.stop()

# Let user choose how many sponsors to display
max_sponsors = len(issues_by_sponsor)
top_n = st.slider(
    "Show top N sponsors by issue count",
    min_value=3,
    max_value=min(50, max_sponsors),
    value=min(20, max_sponsors),
)

top_sponsors = issues_by_sponsor.head(top_n)


fig = px.bar(
    top_sponsors,  # reverse so largest is at top
    x="total_issues",
    y="sponsor",
    orientation="h",
    labels={"total_issues": "Total Issues", "sponsor": "Sponsor"},
    title=f"Top {top_n} Sponsors by Number of Constitutional Issues",
)

fig.update_layout(
    margin={"l": 200, "r": 20, "t": 60, "b": 20},
    height=30 * top_n + 200,
    yaxis=dict(autorange="reversed"),
)

st.plotly_chart(fig, use_container_width=True)
