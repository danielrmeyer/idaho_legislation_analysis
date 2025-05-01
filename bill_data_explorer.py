import streamlit as st
import pandas as pd
import os

datarun = os.getenv("DATARUN")

if not datarun:
    print("Please set the DATARUN environment variable.")

bill_df = pd.read_csv("Data/{datarun}/idaho_bills_{datarun}.csv".format(datarun=datarun))

st.title("Legislation Explorer")
st.dataframe(bill_df)

