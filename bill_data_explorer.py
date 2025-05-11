import streamlit as st
import pandas as pd
import os
from pathlib import Path
from utils import load_data


datarun = os.getenv("DATARUN")

df = load_data()

status_options = ["All"] + sorted(df["bill_status"].dropna().unique().tolist())
sponsor_options = ["All"] + sorted(df["sponsor"].dropna().unique().tolist())

st.title("Idaho Bills by Number of Potential Constitutional Conflicts")
st.markdown(f"""Data scraped on `{datarun}`""")
st.markdown("Please see status codes page for an explanation of the status codes")
selected_status = st.selectbox("Filter by Status", status_options, index=0)
selected_sponsor = st.selectbox("Filter by Sponsor", sponsor_options, index=0)


filtered = df
if selected_status != "All":
    filtered = filtered[filtered["bill_status"] == selected_status]
if selected_sponsor != "All":
    filtered = filtered[filtered["sponsor"] == selected_sponsor]


@st.dialog("Bill Details", width="large")
def show_details(bill_number: str):
    row = df.loc[df["bill_number"] == bill_number].iloc[0]
    st.header(f"{row.bill_number}: {row.bill_title}")
    st.write("**Status:**", row.bill_status)
    st.write("**Sponsor:**", row.sponsor)
    # clickable link
    base_url = "https://legislature.idaho.gov"
    st.markdown(f"[View Full Text]({base_url + row.detail_link})")
    issues = row.json_data or []
    if issues:
        st.subheader("Constitutional Issues")
        for i, issue in enumerate(issues, 1):
            st.markdown(f"**{i}. {issue['issue']}**")
            st.markdown(f"- **References:** {issue['references']}")
            st.markdown(f"- **Explanation:** {issue['explanation']}")
    else:
        st.info("No issues analysis available.")


c1, c2, c3, c4, c5, c6 = st.columns([1, 4, 2, 3, 1, 1])
c1.markdown("**Bill #**")
c2.markdown("**Title**")
c3.markdown("**Status**")
c4.markdown("**Sponsor**")
c5.markdown("**Issues**")
c6.markdown("**Detail**")

for row in filtered.itertuples():
    c1, c2, c3, c4, c5, c6 = st.columns([1, 4, 2, 3, 1, 1])
    c1.write(row.bill_number)
    c2.write(row.bill_title)
    c3.write(row.bill_status)
    c4.write(row.sponsor)
    c5.write(row.issue_count)
    if c6.button("🔍", key=f"btn_{row.bill_number}"):
        show_details(row.bill_number)
