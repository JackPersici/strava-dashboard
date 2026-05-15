from __future__ import annotations

import html
import pandas as pd
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


PANEL_HEIGHT = 430


def _esc(value: object) -> str:
    return html.escape(str(value))


def _empty(message: str = "Nessun dato disponibile.") -> None:
    st.markdown(f"<div class='big-empty'>{_esc(message)}</div>", unsafe_allow_html=True)


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
        f"<span class='sd-card-legend-item'><span class='sd-card-dot' style='background:{color_map.get(sport, '#94A3B8')}'></span>{_esc(sport)}</span>"
        for sport in sports
    )
    return f"<div class='sd-card-legend'>{items}</div>"


def _plotly_fragment(fig, height: int) -> str:
    return fig.to_html(
        include_plotlyjs="cdn",
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
        default_width="100%",
        default_height=f"{height}px",
    )


def _render_monthly_card(fig, legend_html: str, min_width: int = 820, height: int = PANEL_HEIGHT) -> None:
    chart_height = 282
    html_fragment = _plotly_fragment(fig, chart_height)
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
            .sd-card-legend {{display: flex; flex-wrap: wrap; gap: 22px; align-items: center; margin-bottom: 10px; font-size: .80rem; color: #EAF2FF;}}
            .sd-card-legend-item {{display: inline-flex; align-items: center; gap: 8px; white-space: nowrap;}}
            .sd-card-dot {{width: 10px; height: 10px; min-width: 10px; border-radius: 50%; display: inline-block; box-shadow: 0 0 0 2px rgba(255,255,255,0.035);}}
            .sd-scroll-shell {{
                width: 100%;
                height: 300px;
                overflow-x: auto;
                overflow-y: hidden;
                padding-bottom: 10px;
                box-sizing: border-box;
                scrollbar-width: thin;
                scrollbar-color: rgba(226,232,240,0.82) rgba(255,255,255,0.10);
            }}
            .sd-scroll-shell::-webkit-scrollbar {{height: 10px;}}
            .sd-scroll-shell::-webkit-scrollbar-track {{background: rgba(255,255,255,0.10); border-radius: 999px;}}
            .sd-scroll-shell::-webkit-scrollbar-thumb {{background: rgba(226,232,240,0.82); border-radius: 999px;}}
            .sd-scroll-inner {{min-width: {min_width}px; height: {chart_height}px;}}
        </style>
        <div class="sd-card-panel">
            <div class="sd-card-title">Andamento mensile</div>
            <div class="sd-card-subtitle">Distanza aggregata per mese e sport</div>
            {legend_html}
            <div class="sd-scroll-shell">
                <div class="sd-scroll-inner">{html_fragment}</div>
            </div>
        </div>
        """,
        height=height,
        scrolling=False,
    )


def _render_donut_card(fig, height: int = PANEL_HEIGHT) -> None:
    chart_height = 318
    html_fragment = _plotly_fragment(fig, chart_height)
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
            <div class="sd-donut-chart">{html_fragment}</div>
        </div>
        """,
        height=height,
        scrolling=False,
    )



def _activity_dataframe_from_data(data: dict) -> pd.DataFrame | None:
    """Return the most detailed activity dataframe if the app passes it.

    Older versions of the overview received only aggregates, so this helper is
    intentionally defensive: if no activity-level dataframe is available, the
    streak widget degrades gracefully instead of breaking the dashboard.
    """
    for key in ("filtered_df", "activities_df", "activity_df", "df", "raw_df"):
        value = data.get(key)
        if isinstance(value, pd.DataFrame) and not value.empty:
            return value
    return None


def _current_training_week_streak(data: dict) -> int | None:
    df = _activity_dataframe_from_data(data)
    if df is None:
        return None

    date_col = None
    for candidate in ("start_date_local", "start_date", "day"):
        if candidate in df.columns:
            date_col = candidate
            break
    if date_col is None:
        return None

    dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
    if dates.empty:
        return None

    # Weekly streak: count consecutive ISO-like training weeks ending at the
    # latest week present in the filtered data. This mirrors a Strava-style
    # training consistency streak while avoiding assumptions about future weeks.
    weeks = sorted(dates.dt.to_period("W-MON").dropna().unique())
    if not weeks:
        return None

    streak = 1
    cursor = weeks[-1]
    week_set = set(weeks)
    while (cursor - 1) in week_set:
        streak += 1
        cursor = cursor - 1
    return streak


def _key_numbers_html(data: dict, kpis: dict) -> str:
    streak = _current_training_week_streak(data)
    streak_value = "-" if streak is None else str(streak)
    streak_subtitle = "settimane consecutive" if streak != 1 else "settimana consecutiva"

    rows = [
        ("🔥", "fire", streak_value, "streak attuale", streak_subtitle),
        ("🕘", "time", fmt_h(kpis.get("avg_time_h", 0.0)), "media attività", "tempo per attività"),
        ("🗺️", "distance", fmt_km(kpis.get("avg_distance_km", 0.0)), "media distanza", "per attività"),
        ("⛰️", "elevation", fmt_m(kpis.get("avg_elevation_m", 0.0)), "media dislivello", "per attività"),
    ]

    parts = ["<div class='sd-key-card'><div class='sd-key-title'>I tuoi numeri chiave</div><div class='sd-key-list'>"]
    for icon, klass, value, label, subtitle in rows:
        parts.append(
            "<div class='sd-key-row'>"
            f"<div class='sd-key-icon {klass}'>{icon}</div>"
            "<div class='sd-key-copy'>"
            f"<div class='sd-key-value'>{_esc(value)}</div>"
            f"<div class='sd-key-label'>{_esc(label)}</div>"
            f"<div class='sd-key-sub'>{_esc(subtitle)}</div>"
            "</div></div>"
        )
    parts.append("</div></div>")
    return "".join(parts)

def _zone_progress_html(row) -> str:
    zone = _esc(row.get("zone", "Zona"))
    activities = float(row.get("activities_pct", 0.0))
    time_pct = float(row.get("time_pct", 0.0))
    width = max(2.0, min(100.0, time_pct))
    return f"""
    <div class="sd-zone-row">
        <div class="sd-zone-top">
            <div>
                <div class="sd-zone-label">{zone}</div>
                <div class="sd-zone-sub">{activities:.0f}% attività</div>
            </div>
            <div class="sd-zone-value">{time_pct:.0f}% tempo</div>
        </div>
        <div class="sd-zone-track"><div class="sd-zone-fill" style="width:{width:.1f}%"></div></div>
    </div>
    """


def _compact_overview_card(title: str, subtitle: str, body_html: str, height: int = 328) -> str:
    return f"""
    <div class="sd-compact-card" style="min-height:{height}px;">
        <div class="sd-compact-head">
            <h3>{_esc(title)}</h3>
            <p>{_esc(subtitle)}</p>
        </div>
        <div class="sd-compact-body">{body_html}</div>
    </div>
    """


def _inject_overview_final_css() -> None:
    st.markdown(
        """
        <style>
        .sd-compact-card {
            border: 1px solid rgba(216,230,255,0.095);
            border-radius: 18px;
            background: radial-gradient(circle at 20% 0%, rgba(125,183,255,0.045), transparent 17rem), rgba(10,20,34,0.78);
            padding: 16px 18px 14px;
            box-sizing: border-box;
            overflow: hidden;
        }
        .sd-compact-head h3 {
            margin: 0;
            color: #F7FAFF;
            font-size: .98rem;
            letter-spacing: -0.035em;
            font-weight: 830;
        }
        .sd-compact-head p {
            margin: 10px 0 14px;
            color: #AFC0D2;
            font-size: .76rem;
        }
        .sd-compact-body .mini-stat,
        .sd-compact-body .insight-row {
            padding: 8px 9px;
            margin-bottom: 6px;
        }
        .sd-duo-stack {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
        }
        .sd-duo-title {
            color: #F7FAFF;
            font-size: .82rem;
            font-weight: 820;
            margin: 0 0 7px;
            letter-spacing: -0.02em;
        }
        .sd-zone-row {
            border: 1px solid rgba(216,230,255,0.075);
            background: rgba(7,16,28,0.45);
            border-radius: 13px;
            padding: 8px 10px;
            margin-bottom: 7px;
        }
        .sd-zone-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
        }
        .sd-zone-label {
            color: #AFC0D2;
            text-transform: uppercase;
            letter-spacing: .12em;
            font-size: .56rem;
            font-weight: 800;
        }
        .sd-zone-sub {
            color: #8EA2B8;
            font-size: .65rem;
            margin-top: 3px;
        }
        .sd-zone-value {
            color: #F7FAFF;
            font-size: .86rem;
            font-weight: 820;
            white-space: nowrap;
        }
        .sd-zone-track {
            height: 5px;
            border-radius: 999px;
            background: rgba(255,255,255,0.055);
            margin-top: 8px;
            overflow: hidden;
        }
        .sd-zone-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(252,76,2,.86), rgba(139,92,246,.95));
        }

        .sd-key-card {
            border: 1px solid rgba(216,230,255,0.105);
            border-radius: 18px;
            background: radial-gradient(circle at 15% 0%, rgba(125,183,255,0.055), transparent 17rem), rgba(10,20,34,0.82);
            padding: 13px 14px 10px;
            min-height: 316px;
            box-sizing: border-box;
        }
        .sd-key-title {
            color: #F7FAFF;
            font-size: .76rem;
            line-height: 1;
            text-transform: uppercase;
            letter-spacing: .06em;
            font-weight: 860;
            padding: 2px 0 12px;
            border-bottom: 1px solid rgba(216,230,255,0.08);
        }
        .sd-key-list { display: grid; grid-template-columns: 1fr; }
        .sd-key-row {
            display: grid;
            grid-template-columns: 38px minmax(0, 1fr);
            column-gap: 12px;
            align-items: center;
            min-height: 58px;
            padding: 9px 0;
            border-bottom: 1px solid rgba(216,230,255,0.075);
        }
        .sd-key-row:last-child { border-bottom: 0; }
        .sd-key-icon {
            width: 34px;
            height: 34px;
            border-radius: 11px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.05rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
        }
        .sd-key-icon.fire { background: rgba(252,76,2,0.15); color: #FF8A3D; }
        .sd-key-icon.time { background: rgba(14,165,233,0.15); color: #38BDF8; }
        .sd-key-icon.distance { background: rgba(34,197,94,0.14); color: #4ADE80; }
        .sd-key-icon.elevation { background: rgba(139,92,246,0.16); color: #A78BFA; }
        .sd-key-copy { min-width: 0; }
        .sd-key-value {
            color: #F7FAFF;
            font-size: 1.06rem;
            font-weight: 860;
            letter-spacing: -0.035em;
            line-height: 1.05;
        }
        .sd-key-label {
            color: #D8E6F6;
            font-size: .76rem;
            line-height: 1.15;
            margin-top: 2px;
        }
        .sd-key-sub {
            color: #AFC0D2;
            font-size: .68rem;
            line-height: 1.15;
            margin-top: 2px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_overview(data: dict) -> None:
    _inject_overview_final_css()

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
    # ROW 1: Monthly trend + sport distribution
    # =====================================================
    left, right = st.columns([1.82, 1.0], gap="medium")

    with left:
        if monthly_sport_df.empty:
            _empty()
        else:
            legend_html = _sport_legend_html(monthly_sport_df)
            fig = monthly_distance_chart(monthly_sport_df)
            month_count = max(1, monthly_sport_df[["year", "month_num"]].drop_duplicates().shape[0]) if {"year", "month_num"}.issubset(monthly_sport_df.columns) else 12
            _render_monthly_card(fig, legend_html, min_width=max(760, month_count * 40), height=PANEL_HEIGHT)

    with right:
        if sport_summary_df.empty:
            _empty()
        else:
            _render_donut_card(sport_donut_chart(sport_summary_df), height=PANEL_HEIGHT)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # =====================================================
    # ROW 2: compact cumulative trend + compact right rail
    # =====================================================
    t_left, t_right = st.columns([1.82, 1.0], gap="medium")

    with t_left:
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

    with t_right:
        st.markdown(_key_numbers_html(data, kpis), unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # =====================================================
    # ROW 3: bottom widgets
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
                st.markdown(_zone_progress_html(row), unsafe_allow_html=True)
        section_close()
