from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.theme import ACCENT, GREEN, MUTED, PANEL, TEXT, sport_color_map


MONTH_ORDER = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
GRID = "rgba(148,163,184,0.14)"
AXIS = "#9FB0C6"


def plot_style(fig: go.Figure, height: int = 320, show_legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=10, b=8),
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, family="Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT, size=11),
            title_text="",
        ),
        showlegend=show_legend,
        hoverlabel=dict(bgcolor="#17263C", bordercolor="rgba(255,255,255,0.10)", font=dict(color=TEXT)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=AXIS, linecolor="rgba(255,255,255,0.08)", tickfont=dict(color=AXIS))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, color=AXIS, linecolor="rgba(255,255,255,0.08)", tickfont=dict(color=AXIS))
    return fig


def monthly_distance_chart(monthly_sport_df: pd.DataFrame) -> go.Figure:
    temp = monthly_sport_df.copy()
    temp["month"] = pd.Categorical(temp["month"], categories=MONTH_ORDER, ordered=True)
    color_map = sport_color_map(temp["sport_grouped"].dropna().unique())
    fig = px.bar(
        temp.sort_values(["year", "month_num"]),
        x="month",
        y="distance_km",
        color="sport_grouped",
        barmode="stack",
        color_discrete_map=color_map,
        labels={"distance_km": "km", "month": ""},
    )
    fig.update_traces(marker_line_width=0, opacity=0.96, hovertemplate="%{x}<br>%{y:.1f} km<extra></extra>")
    return plot_style(fig, height=365)


def sport_donut_chart(sport_summary_df: pd.DataFrame) -> go.Figure:
    color_map = sport_color_map(sport_summary_df["sport_grouped"].dropna().unique())
    fig = px.pie(
        sport_summary_df,
        names="sport_grouped",
        values="distance_km",
        hole=0.68,
        color="sport_grouped",
        color_discrete_map=color_map,
    )
    fig.update_traces(
        textinfo="percent",
        textfont=dict(color=TEXT, size=12),
        marker=dict(line=dict(color=PANEL, width=2)),
        hovertemplate="%{label}<br>%{value:.1f} km<br>%{percent}<extra></extra>",
    )
    fig.add_annotation(text="Sport", x=0.5, y=0.5, showarrow=False, font=dict(size=13, color=MUTED))
    return plot_style(fig, height=335)


def cumulative_trend_chart(cumulative_metric_df: pd.DataFrame, current_year: int) -> go.Figure:
    temp = cumulative_metric_df.copy()
    temp["year_str"] = temp["year"].astype(str)
    temp["month_label"] = pd.Categorical(temp["month_label"], categories=MONTH_ORDER, ordered=True)
    color_map = {str(y): "#7DB7FF" for y in temp["year"].unique()}
    color_map[str(current_year)] = ACCENT
    fig = px.line(
        temp.sort_values(["year", "month_num"]),
        x="month_label",
        y="cumulative",
        color="year_str",
        markers=True,
        color_discrete_map=color_map,
        category_orders={"month_label": MONTH_ORDER},
        labels={"cumulative": "km", "month_label": ""},
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=7), hovertemplate="%{x}<br>%{y:.1f}<extra></extra>")
    return plot_style(fig, height=350)


def monthly_trend_chart(trend_metric_df: pd.DataFrame, selected_metric: str, current_year: int) -> go.Figure:
    temp = trend_metric_df.copy().sort_values(["year", "month_num"])
    temp["month"] = pd.Categorical(temp["month"], categories=MONTH_ORDER, ordered=True)
    if temp["year"].nunique() > 1:
        temp["year_str"] = temp["year"].astype(str)
        color_map = {str(y): "#7DB7FF" for y in temp["year"].unique()}
        color_map[str(current_year)] = ACCENT
        fig = px.line(temp, x="month", y=selected_metric, color="year_str", markers=True, line_shape="linear", category_orders={"month": MONTH_ORDER}, color_discrete_map=color_map)
    else:
        fig = px.line(temp, x="month", y=selected_metric, markers=True, line_shape="linear", category_orders={"month": MONTH_ORDER})
        fig.update_traces(line=dict(color=ACCENT, width=3))
    fig.update_traces(marker=dict(size=7), hovertemplate="%{x}<br>%{y:.1f}<extra></extra>")
    return plot_style(fig, height=340)


def sport_distance_comparison_chart(sport_summary_df: pd.DataFrame) -> go.Figure:
    color_map = sport_color_map(sport_summary_df["sport_grouped"].dropna().unique())
    fig = px.bar(sport_summary_df.sort_values("distance_km", ascending=True), x="distance_km", y="sport_grouped", orientation="h", color="sport_grouped", color_discrete_map=color_map, labels={"distance_km": "km", "sport_grouped": ""})
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:.1f} km<extra></extra>")
    return plot_style(fig, height=355, show_legend=False)


def buckets_chart(buckets: pd.DataFrame) -> go.Figure:
    fig = px.bar(buckets, x="bucket", y="count", labels={"bucket": "", "count": "attività"})
    fig.update_traces(marker_color=ACCENT, marker_line_width=0)
    return plot_style(fig, height=340, show_legend=False)


def projection_bar_chart(proj: pd.DataFrame) -> go.Figure:
    color_map = sport_color_map(proj["sport_grouped"].dropna().unique())
    fig = px.bar(proj, x="sport_grouped", y="proj_distance_km", color="sport_grouped", color_discrete_map=color_map, labels={"sport_grouped": "", "proj_distance_km": "km"})
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:.1f} km<extra></extra>")
    return plot_style(fig, height=320, show_legend=False)


def progress_gauge(progress: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=progress,
        number={"suffix": "%", "font": {"size": 42, "color": TEXT}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": TEXT, "tickfont": {"color": TEXT}},
            "bar": {"color": GREEN},
            "bgcolor": "#17263C",
            "borderwidth": 0,
            "steps": [{"range": [0, 50], "color": "#13233A"}, {"range": [50, 100], "color": "#1A3151"}],
        },
    ))
    return plot_style(fig, height=265, show_legend=False)


def zones_pie_chart(zones: pd.DataFrame) -> go.Figure:
    zone_colors = {
        "Zona 1 (Recupero)": "#60A5FA",
        "Zona 2 (Endurance)": "#4ADE80",
        "Zona 3 (Tempo)": "#F59E0B",
        "Zona 4 (Soglia)": "#F97316",
        "Zona 5 (VO2 Max)": "#EF4444",
    }
    fig = px.pie(zones, names="zone", values="activities", hole=0.62, color="zone", color_discrete_map=zone_colors)
    fig.update_traces(textinfo="percent", marker=dict(line=dict(color=PANEL, width=2)))
    return plot_style(fig, height=320)


def zones_time_bar_chart(zones: pd.DataFrame) -> go.Figure:
    zone_colors = {
        "Zona 1 (Recupero)": "#60A5FA",
        "Zona 2 (Endurance)": "#4ADE80",
        "Zona 3 (Tempo)": "#F59E0B",
        "Zona 4 (Soglia)": "#F97316",
        "Zona 5 (VO2 Max)": "#EF4444",
    }
    fig = px.bar(zones.sort_values("moving_time_h", ascending=True), x="moving_time_h", y="zone", orientation="h", color="zone", color_discrete_map=zone_colors, labels={"moving_time_h": "ore", "zone": ""})
    fig.update_traces(marker_line_width=0)
    return plot_style(fig, height=320, show_legend=False)


def zones_pct_bar_chart(zones: pd.DataFrame) -> go.Figure:
    zone_colors = {
        "Zona 1 (Recupero)": "#60A5FA",
        "Zona 2 (Endurance)": "#4ADE80",
        "Zona 3 (Tempo)": "#F59E0B",
        "Zona 4 (Soglia)": "#F97316",
        "Zona 5 (VO2 Max)": "#EF4444",
    }
    fig = px.bar(zones, x="zone", y="time_pct", color="zone", color_discrete_map=zone_colors, labels={"zone": "", "time_pct": "% tempo"})
    fig.update_traces(marker_line_width=0)
    return plot_style(fig, height=270, show_legend=False)
