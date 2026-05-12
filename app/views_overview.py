from __future__ import annotations

import streamlit as st

from app.charts import cumulative_trend_chart, monthly_distance_chart, sport_donut_chart
from app.formatters import fmt_h, fmt_int, fmt_km, fmt_m, fmt_pct
from app.theme import card_html, insight_row_html, mini_stat_html, render_header, section_close, section_open


def _empty(message: str = "Nessun dato disponibile.") -> None:
    st.markdown(f"<div class='big-empty'>{message}</div>", unsafe_allow_html=True)


def _metric_delta(value: float) -> str:
    return f"{fmt_pct(value)} vs anno scorso"


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

    render_header(
        title="Strava Dashboard",
        subtitle="Overview personale dei tuoi allenamenti, progressi e insight principali.",
        badges=[
            f"{distance_compare['current_year']}",
            f"{fmt_km(kpis['distance_km'])} totali",
        ],
    )

    # =====================================================
    # TOP KPI
    # =====================================================
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card_html("Attività", fmt_int(kpis["activities"]), _metric_delta(distance_compare["delta_pct"])), unsafe_allow_html=True)
    with c2:
        st.markdown(card_html("Distanza", fmt_km(kpis["distance_km"]), _metric_delta(distance_compare["delta_pct"])), unsafe_allow_html=True)
    with c3:
        st.markdown(card_html("Tempo", fmt_h(kpis["moving_time_h"]), _metric_delta(time_compare["delta_pct"])), unsafe_allow_html=True)
    with c4:
        st.markdown(card_html("Dislivello", fmt_m(kpis["elevation_m"]), _metric_delta(elev_compare["delta_pct"])), unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # =====================================================
    # MAIN GRID
    # =====================================================
    left, right = st.columns([2.05, 1.0], gap="large")

    with left:
        section_open("Andamento mensile", "Distanza aggregata per mese e sport")
        if monthly_sport_df.empty:
            _empty()
        else:
            st.plotly_chart(monthly_distance_chart(monthly_sport_df), use_container_width=True, config={"displayModeBar": False})
        section_close()

        section_open("Trend vs anno scorso", "Confronto cumulativo sulla metrica selezionata")
        if cumulative_metric_df.empty:
            _empty("Nessun confronto disponibile.")
        else:
            st.plotly_chart(
                cumulative_trend_chart(cumulative_metric_df, distance_compare["current_year"]),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.markdown(
                f"<span class='sd-pill'>Sei a {fmt_pct(distance_compare['delta_pct'])} rispetto al {distance_compare['previous_year']}</span>",
                unsafe_allow_html=True,
            )
        section_close()

    with right:
        section_open("Distribuzione sport", "Peso relativo per distanza")
        if sport_summary_df.empty:
            _empty()
        else:
            st.plotly_chart(sport_donut_chart(sport_summary_df), use_container_width=True, config={"displayModeBar": False})
        section_close()

        section_open("Insights", "I segnali più utili del periodo")
        st.markdown(insight_row_html("Sport principale", main_sport["sport"], f"{main_sport['pct']:.0f}% della distanza"), unsafe_allow_html=True)
        st.markdown(insight_row_html("Giorno preferito", fav_day["weekday"], f"{fav_day['pct']:.0f}% delle attività"), unsafe_allow_html=True)
        st.markdown(insight_row_html("Settimana top", active_week.get("week", "-"), f"{active_week.get('activities', 0)} attività"), unsafe_allow_html=True)
        st.markdown(insight_row_html("Costanza", f"{consistency:.0f}/100", "presenza settimanale"), unsafe_allow_html=True)
        section_close()

    # =====================================================
    # BOTTOM GRID
    # =====================================================
    b1, b2 = st.columns([1.25, 1.0], gap="large")

    with b1:
        section_open("Migliori performance", "Record e attività più rilevanti")
        if bp.empty:
            _empty()
        else:
            rows = bp.head(4).to_dict("records")
            for row in rows:
                st.markdown(
                    insight_row_html(
                        str(row.get("label", "Performance")),
                        str(row.get("value", "-")),
                        f"{row.get('date', '-')} · {row.get('sport', '-')}",
                    ),
                    unsafe_allow_html=True,
                )
        section_close()

    with b2:
        section_open("Zone di frequenza", "Distribuzione attività e tempo")
        if zones.empty:
            _empty()
        else:
            for _, row in zones.iterrows():
                st.markdown(
                    insight_row_html(
                        str(row["zone"]),
                        f"{row['time_pct']:.0f}% tempo",
                        f"{row['activities_pct']:.0f}% attività",
                    ),
                    unsafe_allow_html=True,
                )
        section_close()

    # compact summary strip
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(mini_stat_html("Media attività", fmt_km(kpis["avg_distance_km"]), "distanza media"), unsafe_allow_html=True)
    with s2:
        st.markdown(mini_stat_html("Tempo medio", fmt_h(kpis["avg_time_h"]), "per attività"), unsafe_allow_html=True)
    with s3:
        st.markdown(mini_stat_html("Dislivello medio", fmt_m(kpis["avg_elevation_m"]), "per attività"), unsafe_allow_html=True)
