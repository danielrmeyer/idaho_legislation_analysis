"""Shared data-loading helpers used by the Streamlit dashboard pages."""

import streamlit as st
import pandas as pd
from pathlib import Path

from config import get_datarun


@st.cache_data
def load_data():
    """Load the enriched bills JSONL for the current datarun into a DataFrame.

    Calls :func:`config.get_datarun` to resolve the active date string and
    reads the corresponding ``Data/idaho_bills_enriched_<DATARUN>.jsonl``.
    """
    try:
        run = get_datarun()
    except SystemExit:
        st.error(
            "Could not determine DATARUN. "
            "Run scrape.py first or set the DATARUN environment variable."
        )
        st.stop()
    path = Path("Data") / f"idaho_bills_enriched_{run}.jsonl"
    df = pd.read_json(path, orient="records", lines=True)
    return df
