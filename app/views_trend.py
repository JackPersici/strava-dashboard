from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.formatters import fmt_h, fmt_km, fmt_m, fmt_pct


ACCENT = "#ff7a1a"
GREEN = "#22c55e"
TEXT = "#f8fafc"
PANEL = "#0b1830"
MUTED = "#94a3b8"


def section_open(title: str, note: str | None = None) -> None:
    st.markdown(
        f'''
        <div class="panel">
            <div class="panel-title">{title}</div>
            {f'<div class="panel-note">{note}</div>' if note else ""}
        ''',
        unsafe_allow_html=True,
    )


def section_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def mini_stat_html(label: str, value: str, sub: str = "") -> str:
    return f'''
    <div class="mini-stat">
        <div class="mini-label">{label}</div>
        <div class="mini-value">{value}</div>
        <div class="mini-sub">{sub}</div>
    </div>
    '''


def plot_style(fig: go.Figure, height: int = 320, show_legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=12, b=10),
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT),
        ),
        showlegend=show_legend,
    )
    fig.update_xaxes(showgrid=False, color="#cbd5e1")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", color="#cbd5e1")
    return fig


def _cumulative_trend_chart(cumulative_metric_df: pd.DataFrame, current_year: int):
    temp = cumulative_metric_df.copy()
    if temp.empty:
        return go.Figure()

    if "year_str" not in temp.columns:
        temp["year_str"] = temp["year"].astype(str)

    if "month_num" in temp.columns:
        temp = temp.sort_values(["year", "month_num"])

    month_order = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    if "month_label" in temp.columns:
        temp["month_label"] = pd.Categorical(temp["month_label"], categories=month_order, ordered=True)

    color_map = {str(y): "#94c5ff" for y in temp["year"].dropna().unique()}
    color_map[str(current_year)] = ACCENT

    fig = px.line(
        temp,
        x="month_label",
        y="cumulative",
        color="year_str",
        markers=True,
        category_orders={"month_label": month_order},
        color_discrete_map=color_map,
    )
    return plot_style(fig, height=340)


def _monthly_trend_chart(trend_metric_df: pd.DataFrame, selected_metric: str, current_year: int):
    temp = trend_metric_df.copy()
    if temp.empty:
        return go.Figure()

    if "month_num" in temp.columns:
        temp = temp.sort_values(["year", "month_num"])

    month_order = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    if "month" in temp.columns:
        temp["month"] = pd.Categorical(temp["month"], categories=month_order, ordered=True)

    if "year" in temp.columns and temp["year"].nunique() > 1:
        temp["year_str"] = temp["year"].astype(str)
        color_map = {str(y): "#94c5ff" for y in temp["year"].dropna().unique()}
        color_map[str(current_year)] = ACCENT

        fig = px.line(
            temp,
            x="month",
            y=selected_metric,
            color="year_str",
            markers=True,
            line_shape="linear",
            category_orders={"month": month_order},
            color_discrete_map=color_map,
        )
    else:
        fig = px.line(
            temp,
            x="month",
            y=selected_metric,
            markers=True,
            line_shape="linear",
            category_orders={"month": month_order},
        )
        fig.update_traces(line=dict(color=ACCENT, width=3))

    return plot_style(fig, height=340)


def _progress_gauge_chart(progress: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=progress,
            number={"suffix": "%", "font": {"size": 42}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": TEXT},
                "bar": {"color": GREEN},
                "bgcolor": "#16233f",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#1b2b4c"},
                    {"range": [50, 100], "color": "#233559"},
                ],
            },
        )
    )
    return plot_style(fig, height=265, show_legend=False)


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
                _cumulative_trend_chart(
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
                _monthly_trend_chart(
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
            _progress_gauge_chart(progress),
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
