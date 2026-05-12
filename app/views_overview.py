from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from app.charts import cumulative_trend_chart, monthly_distance_chart, sport_donut_chart
from app.formatters import fmt_h, fmt_int, fmt_km, fmt_m, fmt_pct
from app.theme import (
    card_html,
    insight_row_html,
    mini_stat_html,
    overview_topline,
    section_close,
    section_header_html,
    section_open,
    sport_color_map,
)


def _empty(message: str = "Nessun dato disponibile.") -> None:
    st.markdown(f"<div class='big-empty'>{message}</div>", unsafe_allow_html=True)


def _metric_delta(value: float) -> str:
    return f"{fmt_pct(value)} vs anno scorso"


def _plot_config() -> dict:
    return {"displayModeBar": False, "responsive": True}


def _delta_badge(value: float) -> str:
    klass = "green" if value >= 0 else "red"
    return f"<span class='sd-pill {klass}'>{fmt_pct(value)} vs anno scorso</span>"




def _sport_legend_html(df) -> str:
    if df.empty or "sport_grouped" not in df.columns:
        return ""
    available = [str(x) for x in df["sport_grouped"].dropna().unique().tolist()]
    preferred = ["Ciclismo", "Ride", "VirtualRide", "GravelRide", "Altri"]
    sports = [s for s in preferred if s in available] + [s for s in available if s not in preferred]
    color_map = sport_color_map(sports)
    items = "".join(
        f"<span class='sd-chart-legend-item'><span class='sd-chart-dot' style='background:{color_map.get(sport, '#94A3B8')}'></span>{sport}</span>"
        for sport in sports
    )
    return f"<div class='sd-chart-legend horizontal'>{items}</div>"


def _plotly_fragment(fig, height: int) -> str:
    return fig.to_html(
        include_plotlyjs="cdn",
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
        default_width="100%",
        default_height=f"{height}px",
    )


def _render_monthly_card(fig, legend_html: str, min_width: int = 820, height: int = 430) -> None:
    """Single boxed panel: title, subtitle, legend, chart and simple horizontal scrollbar."""
    chart_height = 274
    html = _plotly_fragment(fig, chart_height)
    components.html(
        f"""
        <style>
            .sd-card-panel {{
                width: 100%;
                height: {height}px;
                box-sizing: border-box;
                border: 1px solid rgba(216,230,255,0.095);
                border-radius: 18px;
                background: radial-gradient(circle at 20% 0%, rgba(125,183,255,0.055), transparent 18rem), rgba(10,20,34,0.92);
                padding: 22px 24px 16px 24px;
                overflow: hidden;
                color: #F7FAFF;
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            }}
            .sd-card-title {{font-size: 1.03rem; font-weight: 850; letter-spacing: -0.035em; margin-bottom: 16px;}}
            .sd-card-subtitle {{font-size: .82rem; color: #AFC0D2; margin-bottom: 18px;}}
            .sd-card-legend {{display: flex; flex-wrap: wrap; gap: 22px; align-items: center; margin-bottom: 12px; font-size: .80rem; color: #EAF2FF;}}
            .sd-card-legend .sd-chart-legend-item {{display: inline-flex; align-items: center; gap: 8px; white-space: nowrap;}}
            .sd-card-legend .sd-chart-dot {{width: 10px; height: 10px; border-radius: 50%; display: inline-block; box-shadow: 0 0 0 2px rgba(255,255,255,0.035);}}
            .sd-scroll-shell {{
                width: 100%;
                height: 306px;
                overflow-x: auto;
                overflow-y: hidden;
                padding-bottom: 12px;
                box-sizing: border-box;
                scrollbar-width: thin;
                scrollbar-color: rgba(226,232,240,0.82) rgba(255,255,255,0.10);
            }}
            .sd-scroll-shell::-webkit-scrollbar {{height: 11px;}}
            .sd-scroll-shell::-webkit-scrollbar-track {{background: rgba(255,255,255,0.10); border-radius: 999px;}}
            .sd-scroll-shell::-webkit-scrollbar-thumb {{background: rgba(226,232,240,0.82); border-radius: 999px;}}
            .sd-scroll-inner {{min-width: {min_width}px; height: {chart_height}px;}}
        </style>
        <div class="sd-card-panel">
            <div class="sd-card-title">Andamento mensile</div>
            <div class="sd-card-subtitle">Distanza aggregata per mese e sport</div>
            <div class="sd-card-legend">{legend_html}</div>
            <div class="sd-scroll-shell">
                <div class="sd-scroll-inner">{html}</div>
            </div>
        </div>
        """,
        height=height,
        scrolling=False,
    )


def _render_donut_card(fig, height: int = 430) -> None:
    """Single boxed donut panel, same height as monthly chart."""
    chart_height = 316
    html = _plotly_fragment(fig, chart_height)
    components.html(
        f"""
        <style>
            .sd-donut-panel {{
                width: 100%;
                height: {height}px;
                box-sizing: border-box;
                border: 1px solid rgba(216,230,255,0.095);
                border-radius: 18px;
                background: radial-gradient(circle at 35% 0%, rgba(125,183,255,0.050), transparent 18rem), rgba(10,20,34,0.92);
                padding: 22px 24px 16px 24px;
                overflow: hidden;
                color: #F7FAFF;
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            }}
            .sd-card-title {{font-size: 1.03rem; font-weight: 850; letter-spacing: -0.035em; margin-bottom: 16px;}}
            .sd-card-subtitle {{font-size: .82rem; color: #AFC0D2; margin-bottom: 18px;}}
            .sd-donut-chart {{height: {chart_height}px;}}
        </style>
        <div class="sd-donut-panel">
            <div class="sd-card-title">Distribuzione sport</div>
            <div class="sd-card-subtitle">Peso relativo per distanza</div>
            <div class="sd-donut-chart">{html}</div>
        </div>
        """,
        height=height,
        scrolling=False,
    )


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

    # =====================================================
    # COMPACT PAGE CONTEXT - avoids the duplicated hero effect
    # =====================================================
    st.markdown(
        overview_topline(
            "Overview allenamenti",
            "Volumi, trend e segnali principali dell'anno sportivo.",
            [
                f"{distance_compare['current_year']}",
                f"{fmt_km(kpis['distance_km'])} totali",
                f"{fmt_pct(distance_compare['delta_pct'])}",
            ],
        ),
        unsafe_allow_html=True,
    )

    # =====================================================
    # TOP KPI - compact premium row
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
    left, right = st.columns([1.82, 1.0], gap="medium")

    with left:
        if monthly_sport_df.empty:
            _empty()
        else:
            legend_html = _sport_legend_html(monthly_sport_df)
            fig = monthly_distance_chart(monthly_sport_df)
            month_count = max(1, monthly_sport_df[["year", "month_num"]].drop_duplicates().shape[0]) if {"year", "month_num"}.issubset(monthly_sport_df.columns) else 12
            _render_monthly_card(fig, legend_html, min_width=max(760, month_count * 44), height=430)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(section_header_html("Trend vs anno scorso", "Confronto cumulativo progressivo"), unsafe_allow_html=True)
        if cumulative_metric_df.empty:
            _empty("Nessun confronto disponibile.")
        else:
            st.plotly_chart(
                cumulative_trend_chart(cumulative_metric_df, distance_compare["current_year"]),
                use_container_width=True,
                config=_plot_config(),
            )
            st.markdown(
                f"<div style='margin-top:-2px;margin-bottom:4px;'>{_delta_badge(distance_compare['delta_pct'])}</div>",
                unsafe_allow_html=True,
            )

    with right:
        if sport_summary_df.empty:
            _empty()
        else:
            _render_donut_card(sport_donut_chart(sport_summary_df), height=430)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        section_open("Insights", "Segnali rapidi")
        st.markdown(insight_row_html("Sport principale", main_sport["sport"], f"{main_sport['pct']:.0f}% distanza"), unsafe_allow_html=True)
        st.markdown(insight_row_html("Giorno preferito", fav_day["weekday"], f"{fav_day['pct']:.0f}% attività"), unsafe_allow_html=True)
        st.markdown(insight_row_html("Settimana top", active_week.get("week", "-"), f"{active_week.get('activities', 0)} attività"), unsafe_allow_html=True)
        st.markdown(insight_row_html("Costanza", f"{consistency:.0f}/100", "presenza settimanale"), unsafe_allow_html=True)
        section_close()

        section_open("Medie", "Per singola attività")
        st.markdown(mini_stat_html("Distanza media", fmt_km(kpis["avg_distance_km"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Tempo medio", fmt_h(kpis["avg_time_h"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Dislivello medio", fmt_m(kpis["avg_elevation_m"]), "per attività"), unsafe_allow_html=True)
        section_close()

    # =====================================================
    # BOTTOM GRID
    # =====================================================
    b1, b2 = st.columns([1.28, 1.0], gap="medium")

    with b1:
        section_open("Migliori performance", "Record e attività più rilevanti")
        if bp.empty:
            _empty()
        else:
            for row in bp.head(4).to_dict("records"):
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
