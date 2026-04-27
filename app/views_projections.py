from __future__ import annotations

import streamlit as st

from app.charts import projection_bar_chart
from app.formatters import fmt_h, fmt_int, fmt_km, fmt_m
from app.tables import render_html_table
from app.theme import mini_stat_html, section_close, section_open


def render_projections(data: dict) -> None:
    proj = data["proj"]
    distance_compare = data["distance_compare"]

    a, b = st.columns([1.45, 1.0])

    with a:
        section_open("Proiezione fine anno per sport")
        if proj.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            proj_show = proj[[
                "sport_grouped",
                "proj_distance_km",
                "proj_time_h",
                "proj_elevation_m",
                "proj_activities",
                "delta_distance_pct",
                "delta_time_pct",
                "delta_elevation_pct",
                "delta_activities_pct",
            ]].rename(
                columns={
                    "sport_grouped": "Sport",
                    "proj_distance_km": "Distanza (km)",
                    "proj_time_h": "Tempo (h)",
                    "proj_elevation_m": "Dislivello (m)",
                    "proj_activities": "Attività",
                    "delta_distance_pct": "Δ Distanza %",
                    "delta_time_pct": "Δ Tempo %",
                    "delta_elevation_pct": "Δ Dislivello %",
                    "delta_activities_pct": "Δ Attività %",
                }
            ).copy()
            for col in ["Distanza (km)", "Tempo (h)", "Dislivello (m)", "Attività", "Δ Distanza %", "Δ Tempo %", "Δ Dislivello %", "Δ Attività %"]:
                if col in proj_show.columns:
                    proj_show[col] = proj_show[col].map(lambda x: f"{x:,.1f}")
            render_html_table(proj_show)
        section_close()

        section_open("Proiezione distanza totale")
        if proj.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(projection_bar_chart(proj), use_container_width=True)
        section_close()

    with b:
        section_open("Numeri chiave")
        if proj.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            total_proj_km = float(proj["proj_distance_km"].sum())
            total_proj_h = float(proj["proj_time_h"].sum())
            total_proj_m = float(proj["proj_elevation_m"].sum())
            total_proj_a = float(proj["proj_activities"].sum())
            st.markdown(mini_stat_html("Proiezione distanza", fmt_km(total_proj_km), "anno in corso"), unsafe_allow_html=True)
            st.markdown(mini_stat_html("Proiezione tempo", fmt_h(total_proj_h), "anno in corso"), unsafe_allow_html=True)
            st.markdown(mini_stat_html("Proiezione dislivello", fmt_m(total_proj_m), "anno in corso"), unsafe_allow_html=True)
            st.markdown(mini_stat_html("Proiezione attività", fmt_int(total_proj_a), "anno in corso"), unsafe_allow_html=True)
            prev_total = distance_compare["previous"]
            reach_pct = 100.0 if prev_total <= 0 else min(100.0, (total_proj_km / prev_total) * 100.0)
            st.markdown(
                f"""
                <div class="mini-stat">
                    <div class="mini-label">Probabilità di superare l'anno scorso</div>
                    <div class="mini-value">{reach_pct:.0f}%</div>
                    <div class="mini-sub">con il ritmo attuale</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        section_close()
