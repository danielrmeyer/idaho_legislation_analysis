import streamlit as st
import pandas as pd
import os
from pathlib import Path

# 1) Load & prepare your data
@st.cache_data
def load_data():
    run = os.getenv("DATARUN")
    path = Path("Data")/f"idaho_bills_enriched_{run}.jsonl"
    df = pd.read_json(path, orient="records", lines=True)
    df["issue_count"] = df["json_data"].apply(lambda x: len(x) if isinstance(x, list) else 0)
    return df.sort_values("issue_count", ascending=False)

df = load_data()

st.title("Idaho Bills by Number of Issues")

# 2) Declare the dialog once at top‑level
@st.dialog("Bill Details", width="large")
def show_details(bill_number: str):
    # This function’s body will render inside a modal
    row = df.loc[df["bill_number"] == bill_number].iloc[0]
    st.header(f"{row.bill_number}: {row.bill_title}")
    st.write("**Status:**", row.bill_status)
    st.write("**Sponsor:**", row.sponsor)
    issues = row.json_data or []
    if issues:
        st.subheader("Constitutional Issues")
        for i, issue in enumerate(issues, 1):
            st.markdown(f"**{i}. {issue['issue']}**")
            st.markdown(f"- **References:** {issue['references']}")
            st.markdown(f"- **Explanation:** {issue['explanation']}")
    else:
        st.info("No issues analysis available.")

# 3) Render your table of buttons; call the dialog in the callback
for row in df.itertuples():
    c1, c2, c3, c4 = st.columns([1, 4, 1, 1])
    c1.write(row.bill_number)
    c2.write(row.bill_title)
    c3.write(row.issue_count)
    if c4.button("Details", key=row.bill_number):
        # trigger the dialog
        show_details(row.bill_number)