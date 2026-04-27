from __future__ import annotations

import pandas as pd
import streamlit as st


def render_html_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        return
    html = df.to_html(index=False, classes="data-table", border=0, escape=False)
    st.markdown(f"<div class='table-wrap'>{html}</div>", unsafe_allow_html=True)
