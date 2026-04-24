from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

COLORS = ["#ff7a1a", "#3b82f6", "#60d394", "#ff5d73", "#8b5cf6", "#06b6d4", "#f59e0b", "#94a3b8"]


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1400px;}
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(13,34,51,0.95), rgba(7,19,31,0.95));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 12px 14px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.18);
        }
        .panel {
            background: linear-gradient(180deg, rgba(13,34,51,0.94), rgba(7,19,31,0.94));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 16px 18px 10px 18px;
            margin-bottom: 14px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.18);
        }
        .panel h4 {margin: 0 0 10px 0; font-size: 1rem;}
        .tiny {color: #94a3b8; font-size: 0.85rem;}
        .pill {
            display: inline-block; padding: 5px 10px; border-radius: 999px; background: rgba(255,122,26,0.12);
            color: #ffb16b; border: 1px solid rgba(255,122,26,0.3); font-size: 0.82rem; margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(fig: go.Figure, height: int = 330) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        font=dict(color="#e5eef7"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
    return fig


def render_kpis(kpis: dict[str, dict[str, str | float]]) -> None:
    cols = st.columns(len(kpis))
    for col, (label, payload) in zip(cols, kpis.items()):
        with col:
            st.metric(label, payload["value"], payload["delta"])


def stacked_monthly_chart(df: pd.DataFrame, value_col: str = "distance_km", title: str = "") -> None:
    if df.empty:
        st.info("Nessun dato disponibile.")
        return
    fig = px.bar(
        df,
        x="month",
        y=value_col,
        color="sport_label",
        color_discrete_sequence=COLORS,
        barmode="stack",
        title=title,
    )
    fig = chart_layout(fig, height=320)
    st.plotly_chart(fig, width="stretch")


def donut_sport_distribution(df: pd.DataFrame, value_col: str = "distance_km") -> None:
    if df.empty:
        st.info("Nessun dato disponibile.")
        return
    fig = px.pie(
        df,
        values=value_col,
        names="sport_label",
        hole=0.62,
        color_discrete_sequence=COLORS,
    )
    fig = chart_layout(fig, height=320)
    st.plotly_chart(fig, width="stretch")


def line_comparison(df: pd.DataFrame, x: str, y: str, color: str, title: str = "") -> None:
    if df.empty:
        st.info("Nessun dato disponibile.")
        return
    fig = px.line(df, x=x, y=y, color=color, color_discrete_sequence=COLORS, title=title)
    fig = chart_layout(fig, height=300)
    st.plotly_chart(fig, width="stretch")


def multi_metric_trend(df: pd.DataFrame, metric: str) -> None:
    if df.empty:
        st.info("Nessun dato disponibile.")
        return
    fig = px.line(df, x="month", y=metric, color="sport_label", markers=True, color_discrete_sequence=COLORS)
    fig = chart_layout(fig, height=320)
    st.plotly_chart(fig, width="stretch")


def horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str = "") -> None:
    if df.empty:
        st.info("Nessun dato disponibile.")
        return
    fig = px.bar(df, x=x, y=y, orientation="h", color_discrete_sequence=[COLORS[1]], title=title)
    fig = chart_layout(fig, height=320)
    st.plotly_chart(fig, width="stretch")


def small_info_card(title: str, text: str) -> None:
    st.markdown(f"<div class='panel'><h4>{title}</h4><div>{text}</div></div>", unsafe_allow_html=True)


def table(df: pd.DataFrame, height: int = 360) -> None:
    st.dataframe(df, width="stretch", hide_index=True, height=height)
