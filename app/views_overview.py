from __future__ import annotations

import streamlit as st

from app.charts import cumulative_trend_chart, monthly_distance_chart, sport_donut_chart
from app.formatters import fmt_h, fmt_int, fmt_km, fmt_m, fmt_pct
from app.theme import card_html, mini_stat_html, section_close, section_open


def render_overview(data: dict) -> None:
    kpis = data["kpis"]
    distance_compare = data["distance_compare"]
    time_compare = data["time_compare"]
    elev_compare = data["elev_compare"]
    monthly_sport_df = data["monthly_sport_df"]
    sport_summary_df = data["sport_summary_df"]
    cumulative_metric_df = data["cumulative_metric_df"]
    bp = data["best_performances"]
    zones = data["zones"]
    fav_day = data["favorite_weekday"]
    active_week = data["most_active_week"]
    main_sport = data["primary_sport"]
    consistency = data["consistency"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card_html("Attività", fmt_int(kpis["activities"]), f"{fmt_pct(distance_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)
    with c2:
        st.markdown(card_html("Distanza", fmt_km(kpis["distance_km"]), f"{fmt_pct(distance_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)
    with c3:
        st.markdown(card_html("Tempo", fmt_h(kpis["moving_time_h"]), f"{fmt_pct(time_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)
    with c4:
        st.markdown(card_html("Dislivello", fmt_m(kpis["elevation_m"]), f"{fmt_pct(elev_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)

    a, b, c = st.columns([1.9, 1.15, 0.95])

    with a:
        section_open("Andamento mensile", "Distanza aggregata per mese e sport")
        if monthly_sport_df.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(monthly_distance_chart(monthly_sport_df), use_container_width=True)
        section_close()

    with b:
        section_open("Distribuzione distanza per sport")
        if sport_summary_df.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(sport_donut_chart(sport_summary_df), use_container_width=True)
        section_close()

    with c:
        section_open("I tuoi numeri chiave")
        st.markdown(mini_stat_html("Attività", fmt_int(kpis["activities"]), "totale periodo selezionato"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Media distanza", fmt_km(kpis["avg_distance_km"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Media tempo", fmt_h(kpis["avg_time_h"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Media dislivello", fmt_m(kpis["avg_elevation_m"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Indice di costanza", f"{consistency:.0f}/100", "presenza settimanale"), unsafe_allow_html=True)
        section_close()

    d, e, f = st.columns([1.4, 1.05, 1.0])

    with d:
        section_open("Trend vs anno scorso", "Confronto cumulativo")
        if cumulative_metric_df.empty:
            st.markdown("<div class='big-empty'>Nessun confronto disponibile.</div>", unsafe_allow_html=True)
        else:
            st.plotly_chart(cumulative_trend_chart(cumulative_metric_df, distance_compare["current_year"]), use_container_width=True)
            st.markdown(f"<span class='pill'>Sei a {fmt_pct(distance_compare['delta_pct'])} rispetto al {distance_compare['previous_year']}</span>", unsafe_allow_html=True)
        section_close()

    with e:
        section_open("Migliori performance")
        if bp.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            for _, row in bp.iterrows():
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{row['value']}</div>
                        <div class="insight-sub">{row['label']} · {row['date']} · {row['sport']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()

    with f:
        section_open("Zone di frequenza", "Distribuzione attività")
        if zones.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            for _, row in zones.iterrows():
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{row['zone']}</div>
                        <div class="insight-sub">{row['activities_pct']:.0f}% attività · {row['time_pct']:.0f}% tempo</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()

    g, h, i = st.columns(3)
    with g:
        st.markdown(mini_stat_html("Giorno preferito", fav_day["weekday"], f"{fav_day['pct']:.0f}% delle attività"), unsafe_allow_html=True)
    with h:
        st.markdown(mini_stat_html("Settimana più attiva", active_week.get("week", "-"), f"{active_week.get('activities', 0)} attività"), unsafe_allow_html=True)
    with i:
        st.markdown(mini_stat_html("Sport principale", main_sport["sport"], f"{main_sport['pct']:.0f}% della distanza"), unsafe_allow_html=True)
