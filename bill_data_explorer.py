"""Main Streamlit dashboard — ranks Idaho bills by potential constitutional issues.

This is the multipage app entrypoint.  Run with::

    uv run streamlit run bill_data_explorer.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from utils import load_data
from config import get_datarun


datarun = get_datarun()

df = load_data()

status_options = ["All"] + sorted(df["bill_status"].dropna().unique().tolist())
sponsor_options = ["All"] + sorted(df["sponsor"].dropna().unique().tolist())

st.title("Idaho Bills – Ranked by Potential Constitutional Issues")
st.markdown("""
## About This App

This dashboard uses the **OpenAI API** to scan every bill in the current Idaho legislative session for potential constitutional conflicts. 

- **Data Source**  
  Bills are fetched and enriched via a scraper.

- **Issue Detection**  
  Each bill’s text is analyzed by OpenAI to surface possible issues (e.g. equal‑protection, due‑process, federal preemption).  

- **Ranking**  
  Bills are ranked by their **number of detected issues**.

- **Filtering**  
  Use the **Status** and **Sponsor** selectors to narrow the list.  

- **Detail View**  
  Click the 🔍 icon in any row to open the **Bill Details** dialog. There you’ll find:  
  - A link to the official bill text on the Idaho Legislature website  
  - A full list of identified issues, with references and explanations  

""")
st.markdown("Please see status codes page for an explanation of the status codes")
st.markdown(f"""Data scraped on `{datarun}`""")
selected_status = st.selectbox("Filter by Status", status_options, index=0)
selected_sponsor = st.selectbox("Filter by Sponsor", sponsor_options, index=0)


filtered = df
if selected_status != "All":
    filtered = filtered[filtered["bill_status"] == selected_status]
if selected_sponsor != "All":
    filtered = filtered[filtered["sponsor"] == selected_sponsor]


@st.dialog("Bill Details", width="large")
def show_details(bill_number: str):
    """Open a modal dialog showing full details and constitutional issues for a bill."""
    row = df.loc[df["bill_number"] == bill_number].iloc[0]
    st.header(f"{row.bill_number}: {row.bill_title}")
    st.write("**Status:**", row.bill_status)
    st.write("**Sponsor:**", row.sponsor)
    # clickable link
    base_url = "https://legislature.idaho.gov"
    st.markdown(f"[View Full Text]({base_url + row.detail_link})")
    issues = row.json_data or []
    if issues:
        st.subheader("Possible Constitutional Issues")
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
