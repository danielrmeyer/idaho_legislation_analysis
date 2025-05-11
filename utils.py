import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pathlib import Path


@st.cache_data
def load_data():
    run = os.getenv("DATARUN")
    if not run:
        st.error("Please set DATARUN in your environment.")
        st.stop()
    path = Path("Data") / f"idaho_bills_enriched_{run}.jsonl"
    df = pd.read_json(path, orient="records", lines=True)
    return df
