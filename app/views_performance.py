from __future__ import annotations

import pandas as pd
import streamlit as st

from app.charts import buckets_chart
from app.theme import section_close, section_open


def render_performance(data: dict, filtered_df: pd.DataFrame) -> None:
    buckets = data["buckets"]
    records = data["records"]

    a, b, c = st.columns([1.0, 1.1, 0.95])

    with a:
        section_open("Top 5 - più lunghe distanze")
        top5 = filtered_df.sort_values("distance_km", ascending=False).head(5).copy()
        if top5.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            top5["date_str"] = pd.to_datetime(top5["start_date_local"]).dt.strftime("%d %b %Y")
            for idx, (_, row) in enumerate(top5.iterrows(), start=1):
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{idx}. {row['distance_km']:.1f} km</div>
                        <div class="insight-sub">{row.get('sport_grouped', row['sport_label'])} · {row['date_str']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()

    with b:
        section_open("Distribuzione attività per distanza")
        if buckets.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(buckets_chart(buckets), use_container_width=True)
        section_close()

    with c:
        section_open("Record personali")
        if records.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            for _, row in records.iterrows():
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{row['record']}</div>
                        <div class="insight-sub">{row['value']} · {row['date']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()
