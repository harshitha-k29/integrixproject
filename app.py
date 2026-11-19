# app.py - owner: Coder 2
import pandas as pd
import streamlit as st

from detect import detect_issues
from repair import repair

st.title("DataFix")

uploaded = st.file_uploader("Upload a messy CSV", type="csv")

if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.subheader("Original data")
    st.dataframe(df)

    issues = detect_issues(df)
    st.subheader("Issues found: " + str(len(issues)))
    st.dataframe(pd.DataFrame(issues))

    clean_df, change_log, needs_review = repair(df, issues)
    st.subheader("Cleaned data")
    st.dataframe(clean_df)