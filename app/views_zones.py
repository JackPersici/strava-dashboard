from __future__ import annotations

import pandas as pd
import streamlit as st

from app.charts import zones_pct_bar_chart, zones_pie_chart, zones_time_bar_chart
from app.theme import mini_stat_html, section_close, section_open


def render_zones(data: dict, filtered_df: pd.DataFrame) -> None:
    zones = data["zones"]

    a, b = st.columns([1.0, 1.0])
    with a:
        section_open("Distribuzione attività per zona")
        if zones.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(zones_pie_chart(zones), use_container_width=True)
        section_close()

    with b:
        section_open("Tempo in zona (ore)")
        if zones.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(zones_time_bar_chart(zones), use_container_width=True)
        section_close()

    if not zones.empty:
        zone2_pct = float(zones.loc[zones["zone"] == "Zona 2 (Endurance)", "time_pct"].sum()) if "Zona 2 (Endurance)" in zones["zone"].astype(str).tolist() else 0.0
        avg_intensity = float(filtered_df["effort_score"].mean()) if "effort_score" in filtered_df.columns else 0.0
        weekly_load = float(filtered_df.groupby(["year", "week"])["moving_time_h"].sum().mean()) if not filtered_df.empty else 0.0
        trend_int = float(filtered_df["effort_score"].tail(min(10, len(filtered_df))).mean()) if not filtered_df.empty else 0.0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(mini_stat_html("Intensità media", f"{avg_intensity:.1f}", "su 5 zone proxy"), unsafe_allow_html=True)
        with c2:
            st.markdown(mini_stat_html("Attività in zona 2", f"{zone2_pct:.0f}%", "tempo in zona 2"), unsafe_allow_html=True)
        with c3:
            st.markdown(mini_stat_html("Carico settimanale", f"{weekly_load:.1f} h", "media ultime settimane"), unsafe_allow_html=True)
        with c4:
            st.markdown(mini_stat_html("Trend intensità", f"{trend_int:.0f}", "proxy score recente"), unsafe_allow_html=True)
        section_open("Distribuzione tempo in zona (%)")
        st.plotly_chart(zones_pct_bar_chart(zones), use_container_width=True)
        section_close()
