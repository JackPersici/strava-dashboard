from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.theme import ACCENT, GREEN, MUTED, PANEL, TEXT, sport_color_map


MONTH_ORDER = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
GRID = "rgba(148,163,184,0.095)"
AXIS = "#8CA0B8"
TRANSPARENT = "rgba(0,0,0,0)"


def plot_style(fig: go.Figure, height: int = 270, show_legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=4, r=4, t=2, b=2),
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        font=dict(color=TEXT, family="Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif", size=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            x=0,
            bgcolor=TRANSPARENT,
            font=dict(color=MUTED, size=9),
            title_text="",
            itemwidth=30,
        ),
        showlegend=show_legend,
        hoverlabel=dict(
            bgcolor="#16263D",
            bordercolor="rgba(255,255,255,0.10)",
            font=dict(color=TEXT, size=11),
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        color=AXIS,
        tickfont=dict(color=AXIS, size=9),
        title_font=dict(color=MUTED, size=9),
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False,
        showline=False,
        color=AXIS,
        tickfont=dict(color=AXIS, size=9),
        title_font=dict(color=MUTED, size=9),
    )
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
        labels={"month": "", "distance_km": "km", "sport_grouped": ""},
    )
    fig.update_traces(marker_line_width=0, opacity=0.94, hovertemplate="%{x}<br>%{y:.1f} km<extra></extra>")
    fig.update_layout(bargap=0.38)
    return plot_style(fig, height=255)


def sport_donut_chart(sport_summary_df: pd.DataFrame) -> go.Figure:
    color_map = sport_color_map(sport_summary_df["sport_grouped"].dropna().unique())
    fig = px.pie(
        sport_summary_df,
        names="sport_grouped",
        values="distance_km",
        hole=0.70,
        color="sport_grouped",
        color_discrete_map=color_map,
    )
    fig.update_traces(
        textinfo="percent",
        textfont=dict(size=10, color=TEXT),
        marker=dict(line=dict(color=PANEL, width=2)),
        hovertemplate="%{label}<br>%{value:.1f} km<br>%{percent}<extra></extra>",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", y=1.04, x=0, font=dict(size=9, color=MUTED), title_text=""),
        annotations=[dict(text="Sport", x=0.5, y=0.5, showarrow=False, font=dict(size=10, color=MUTED))],
    )
    return plot_style(fig, height=228)


def cumulative_trend_chart(cumulative_metric_df: pd.DataFrame, current_year: int) -> go.Figure:
    temp = cumulative_metric_df.copy()
    temp["year_str"] = temp["year"].astype(str)
    temp["month_label"] = pd.Categorical(temp["month_label"], categories=MONTH_ORDER, ordered=True)
    color_map = {str(y): "rgba(125,183,255,0.72)" for y in temp["year"].dropna().unique()}
    color_map[str(current_year)] = ACCENT
    fig = px.line(
        temp.sort_values(["year", "month_num"]),
        x="month_label",
        y="cumulative",
        color="year_str",
        markers=True,
        color_discrete_map=color_map,
        category_orders={"month_label": MONTH_ORDER},
        labels={"month_label": "", "cumulative": "totale", "year_str": ""},
    )
    fig.update_traces(line=dict(width=2.2), marker=dict(size=5.4), hovertemplate="%{x}<br>%{y:.1f}<extra></extra>")
    return plot_style(fig, height=255)


def monthly_trend_chart(trend_metric_df: pd.DataFrame, selected_metric: str, current_year: int) -> go.Figure:
    temp = trend_metric_df.copy().sort_values(["year", "month_num"])
    temp["month"] = pd.Categorical(temp["month"], categories=MONTH_ORDER, ordered=True)
    if temp["year"].nunique() > 1:
        temp["year_str"] = temp["year"].astype(str)
        color_map = {str(y): "rgba(125,183,255,0.72)" for y in temp["year"].dropna().unique()}
        color_map[str(current_year)] = ACCENT
        fig = px.line(
            temp,
            x="month",
            y=selected_metric,
            color="year_str",
            markers=True,
            line_shape="linear",
            category_orders={"month": MONTH_ORDER},
            color_discrete_map=color_map,
            labels={"month": "", selected_metric: "", "year_str": ""},
        )
    else:
        fig = px.line(
            temp,
            x="month",
            y=selected_metric,
            markers=True,
            line_shape="linear",
            category_orders={"month": MONTH_ORDER},
            labels={"month": "", selected_metric: ""},
        )
        fig.update_traces(line=dict(color=ACCENT, width=2.3))
    fig.update_traces(marker=dict(size=5.4), hovertemplate="%{x}<br>%{y:.1f}<extra></extra>")
    return plot_style(fig, height=255)


def sport_distance_comparison_chart(sport_summary_df: pd.DataFrame) -> go.Figure:
    color_map = sport_color_map(sport_summary_df["sport_grouped"].dropna().unique())
    fig = px.bar(
        sport_summary_df.sort_values("distance_km", ascending=True),
        x="distance_km",
        y="sport_grouped",
        orientation="h",
        color="sport_grouped",
        color_discrete_map=color_map,
        labels={"distance_km": "km", "sport_grouped": ""},
    )
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:.1f} km<extra></extra>")
    return plot_style(fig, height=285, show_legend=False)


def buckets_chart(buckets: pd.DataFrame) -> go.Figure:
    fig = px.bar(buckets, x="bucket", y="count", labels={"bucket": "", "count": "attività"})
    fig.update_traces(marker_color=ACCENT, marker_line_width=0, hovertemplate="%{x}<br>%{y} attività<extra></extra>")
    fig.update_layout(bargap=0.38)
    return plot_style(fig, height=270, show_legend=False)


def projection_bar_chart(proj: pd.DataFrame) -> go.Figure:
    color_map = sport_color_map(proj["sport_grouped"].dropna().unique())
    fig = px.bar(
        proj,
        x="sport_grouped",
        y="proj_distance_km",
        color="sport_grouped",
        color_discrete_map=color_map,
        labels={"sport_grouped": "", "proj_distance_km": "km"},
    )
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:.1f} km<extra></extra>")
    return plot_style(fig, height=270, show_legend=False)


def progress_gauge(progress: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=progress,
            number={"suffix": "%", "font": {"size": 32, "color": TEXT}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": MUTED, "tickfont": {"color": MUTED, "size": 9}},
                "bar": {"color": GREEN},
                "bgcolor": "rgba(255,255,255,0.035)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "rgba(143,161,184,0.09)"},
                    {"range": [50, 100], "color": "rgba(34,197,94,0.11)"},
                ],
            },
        )
    )
    return plot_style(fig, height=218, show_legend=False)


def zones_pie_chart(zones: pd.DataFrame) -> go.Figure:
    zone_colors = {
        "Zona 1 (Recupero)": "#60A5FA",
        "Zona 2 (Endurance)": "#4ADE80",
        "Zona 3 (Tempo)": "#F59E0B",
        "Zona 4 (Soglia)": "#F97316",
        "Zona 5 (VO2 Max)": "#EF4444",
    }
    fig = px.pie(zones, names="zone", values="activities", hole=0.68, color="zone", color_discrete_map=zone_colors)
    fig.update_traces(textinfo="percent", marker=dict(line=dict(color=PANEL, width=2)), hovertemplate="%{label}<br>%{value} attività<br>%{percent}<extra></extra>")
    return plot_style(fig, height=260)


def zones_time_bar_chart(zones: pd.DataFrame) -> go.Figure:
    zone_colors = {
        "Zona 1 (Recupero)": "#60A5FA",
        "Zona 2 (Endurance)": "#4ADE80",
        "Zona 3 (Tempo)": "#F59E0B",
        "Zona 4 (Soglia)": "#F97316",
        "Zona 5 (VO2 Max)": "#EF4444",
    }
    fig = px.bar(
        zones.sort_values("moving_time_h", ascending=True),
        x="moving_time_h",
        y="zone",
        orientation="h",
        color="zone",
        color_discrete_map=zone_colors,
        labels={"moving_time_h": "ore", "zone": ""},
    )
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:.1f} h<extra></extra>")
    return plot_style(fig, height=260, show_legend=False)


def zones_pct_bar_chart(zones: pd.DataFrame) -> go.Figure:
    zone_colors = {
        "Zona 1 (Recupero)": "#60A5FA",
        "Zona 2 (Endurance)": "#4ADE80",
        "Zona 3 (Tempo)": "#F59E0B",
        "Zona 4 (Soglia)": "#F97316",
        "Zona 5 (VO2 Max)": "#EF4444",
    }
    fig = px.bar(zones, x="zone", y="time_pct", color="zone", color_discrete_map=zone_colors, labels={"zone": "", "time_pct": "% tempo"})
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:.0f}%<extra></extra>")
    return plot_style(fig, height=230, show_legend=False)
