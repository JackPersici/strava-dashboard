from __future__ import annotations

import streamlit as st

from app.charts import sport_distance_comparison_chart
from app.formatters import fmt_h, fmt_km, fmt_m
from app.tables import render_html_table
from app.theme import mini_stat_html, section_close, section_open


def render_per_sport(data: dict) -> None:
    sport_summary_df = data["sport_summary_df"]
    top_sports = data["top_sports"]
    kpis = data["kpis"]

    a, b = st.columns([2.0, 0.95])

    with a:
        section_open("Riepilogo per sport")
        show = sport_summary_df.rename(
            columns={
                "sport_grouped": "Sport",
                "activities": "Attività",
                "distance_km": "Distanza (km)",
                "moving_time_h": "Tempo (h)",
                "elevation_m": "Dislivello (m)",
                "avg_speed_kmh": "Vel. media",
            }
        ).copy()
        for col in ["Distanza (km)", "Tempo (h)", "Dislivello (m)", "Vel. media"]:
            if col in show.columns:
                show[col] = show[col].map(lambda x: f"{x:,.1f}")
        render_html_table(show)
        section_close()

        section_open("Confronto distanza per sport")
        if sport_summary_df.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(sport_distance_comparison_chart(sport_summary_df), use_container_width=True)
        section_close()

    with b:
        section_open("Top sport")
        st.markdown("<div class='tiny' style='margin-bottom:8px;'>per distanza</div>", unsafe_allow_html=True)
        for r in top_sports["distance"]:
            st.markdown(f"<div class='insight-row'><div class='insight-main'>{r['sport_label']}</div><div class='insight-sub'>{fmt_km(r['distance_km'])}</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='tiny' style='margin-top:10px; margin-bottom:8px;'>per tempo</div>", unsafe_allow_html=True)
        for r in top_sports["time"]:
            st.markdown(f"<div class='insight-row'><div class='insight-main'>{r['sport_label']}</div><div class='insight-sub'>{fmt_h(r['moving_time_h'])}</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='tiny' style='margin-top:10px; margin-bottom:8px;'>per dislivello</div>", unsafe_allow_html=True)
        for r in top_sports["elevation"]:
            st.markdown(f"<div class='insight-row'><div class='insight-main'>{r['sport_label']}</div><div class='insight-sub'>{fmt_m(r['elevation_m'])}</div></div>", unsafe_allow_html=True)
        section_close()

        target_distance = max(1.0, kpis["distance_km"] * 1.5)
        progress_pct = min(100.0, (kpis["distance_km"] / target_distance) * 100.0)
        st.markdown(mini_stat_html("Obiettivo annuale", f"{progress_pct:.0f}%", f"{fmt_km(kpis['distance_km'])} / {fmt_km(target_distance)}"), unsafe_allow_html=True)
