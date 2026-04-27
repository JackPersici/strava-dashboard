from __future__ import annotations

import streamlit as st

from app.charts import (
    cumulative_trend_chart,
    monthly_trend_chart,
    progress_gauge_chart,
)
from app.formatters import fmt_km, fmt_h, fmt_m, fmt_pct
from app.theme import section_open, section_close, mini_stat_html


def render_trend(prepared: dict, metric_label: str, selected_metric: str) -> None:
    kpis = prepared["kpis"]
    distance_compare = prepared["distance_compare"]
    time_compare = prepared["time_compare"]
    elev_compare = prepared["elev_compare"]

    cumulative_metric_df = prepared["cumulative_metric_df"]
    trend_metric_df = prepared["trend_metric_df"]

    month_best_worst = prepared["month_best_worst"]
    consistency = prepared["consistency"]

    a, b = st.columns([1.95, 1.0])

    with a:
        section_open("Trend cumulativo")

        if not cumulative_metric_df.empty:
            st.plotly_chart(
                cumulative_trend_chart(
                    cumulative_metric_df,
                    distance_compare["current_year"],
                ),
                use_container_width=True,
                key="trend_cumulative_chart",
            )
        else:
            st.info("Nessun dato disponibile")

        section_close()

        section_open("Trend mensile", f"Metrica: {metric_label}")

        if not trend_metric_df.empty:
            st.plotly_chart(
                monthly_trend_chart(
                    trend_metric_df,
                    selected_metric,
                    distance_compare["current_year"],
                ),
                use_container_width=True,
                key="trend_monthly_chart",
            )
        else:
            st.info("Nessun dato disponibile")

        section_close()

    with b:
        section_open("Progresso")

        target_value = max(
            1.0,
            distance_compare["previous"] * 1.10
            if distance_compare["previous"] > 0
            else kpis["distance_km"] * 1.25,
        )

        progress = min(100.0, (kpis["distance_km"] / target_value) * 100.0)

        st.plotly_chart(
            progress_gauge_chart(progress),
            use_container_width=True,
            key="trend_progress_gauge",
        )

        st.markdown(
            f"<div class='tiny'>{fmt_km(kpis['distance_km'])} distanza percorsa</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='tiny'>su target {fmt_km(target_value)}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            mini_stat_html(
                "Miglior mese",
                month_best_worst["best_month"],
                fmt_km(month_best_worst["best_value"]),
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            mini_stat_html(
                "Peggior mese",
                month_best_worst["worst_month"],
                fmt_km(month_best_worst["worst_value"]),
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            mini_stat_html(
                "Stabilità",
                f"{consistency:.0f}/100",
                "indice di costanza",
            ),
            unsafe_allow_html=True,
        )

        section_close()

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Distanza totale",
            fmt_km(kpis["distance_km"]),
            fmt_pct(distance_compare["delta_pct"]),
        )

    with m2:
        st.metric(
            "Tempo totale",
            fmt_h(kpis["moving_time_h"]),
            fmt_pct(time_compare["delta_pct"]),
        )

    with m3:
        st.metric(
            "Dislivello totale",
            fmt_m(kpis["elevation_m"]),
            fmt_pct(elev_compare["delta_pct"]),
        )

    with m4:
        st.metric(
            "Attività totali",
            f"{int(round(kpis['activities']))}",
        )
