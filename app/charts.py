from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.theme import ACCENT, GREEN, MUTED, PANEL, TEXT, sport_color_map


MONTH_ORDER = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
GRID = "rgba(148,163,184,0.065)"
AXIS = "#7F93A9"
TRANSPARENT = "rgba(0,0,0,0)"


def plot_style(fig: go.Figure, height: int = 270, show_legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=4, r=4, t=0, b=2),
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        font=dict(color=TEXT, family="Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif", size=9),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0.02,
            bgcolor=TRANSPARENT,
            font=dict(color=MUTED, size=8),
            title_text="",
            itemsizing="constant",
            itemwidth=58,
            tracegroupgap=6,
        ),
        showlegend=show_legend,
        hoverlabel=dict(
            bgcolor="#16263D",
            bordercolor="rgba(255,255,255,0.10)",
            font=dict(color=TEXT, size=10),
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        color=AXIS,
        tickfont=dict(color=AXIS, size=8),
        title_font=dict(color=MUTED, size=8),
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False,
        showline=False,
        color=AXIS,
        tickfont=dict(color=AXIS, size=8),
        title_font=dict(color=MUTED, size=8),
    )
    return fig

def _legend_circle_traces(fig: go.Figure, color_map: dict[str, str]) -> go.Figure:
    """Use invisible scatter traces so Plotly legends render circular markers."""
    names: list[str] = []
    for trace in fig.data:
        name = getattr(trace, "name", None)
        if name and name not in names:
            names.append(str(name))
        trace.showlegend = False

    for name in names:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=name,
                marker=dict(size=8, color=color_map.get(name, MUTED), symbol="circle"),
                hoverinfo="skip",
                showlegend=True,
            )
        )
    return fig


def period_metric_chart(period_df: pd.DataFrame, value_col: str = "distance_km") -> go.Figure:
    temp = period_df.copy()
    if temp.empty:
        return go.Figure()

    if value_col not in temp.columns:
        value_col = "distance_km" if "distance_km" in temp.columns else temp.select_dtypes("number").columns[-1]

    if "period_label" not in temp.columns:
        temp = temp.dropna(subset=["year", "month_num"]).copy()
        if temp.empty:
            return go.Figure()
        temp["year"] = temp["year"].astype(int)
        temp["month_num"] = temp["month_num"].astype(int)
        temp["month"] = temp["month_num"].map(lambda n: MONTH_ORDER[int(n) - 1])
        temp["period_label"] = temp["month"] + "<br>" + temp["year"].astype(str)
        temp["period_sort"] = temp["year"] * 100 + temp["month_num"]
    else:
        temp = temp.dropna(subset=["period_label"]).copy()
        if "period_sort" not in temp.columns:
            sort_cols = [c for c in ["year", "week", "month_num"] if c in temp.columns]
            if sort_cols:
                temp["period_sort"] = temp[sort_cols].astype(int).astype(str).agg("-".join, axis=1)
            else:
                temp["period_sort"] = range(len(temp))

    temp = (
        temp.groupby(["period_label", "period_sort", "sport_grouped"], as_index=False, dropna=False)
        .agg(value=(value_col, "sum"))
        .sort_values("period_sort")
    )
    if temp.empty:
        return go.Figure()

    periods_df = temp[["period_label", "period_sort"]].drop_duplicates().sort_values("period_sort").reset_index(drop=True)
    period_order = periods_df["period_label"].astype(str).tolist()
    period_idx = {label: i for i, label in enumerate(period_order)}

    preferred_order = ["Ciclismo", "Ride", "VirtualRide", "GravelRide", "Corsa", "Run", "Escursionismo", "Hike", "Altri"]
    available = [str(x) for x in temp["sport_grouped"].dropna().unique().tolist()]
    sports = [s for s in preferred_order if s in available] + [s for s in available if s not in preferred_order]
    if not sports:
        return go.Figure()

    full_index = periods_df.merge(pd.DataFrame({"sport_grouped": sports}), how="cross")
    temp = full_index.merge(temp, on=["period_label", "period_sort", "sport_grouped"], how="left")
    temp["value"] = temp["value"].fillna(0.0)
    temp["period_label"] = temp["period_label"].astype(str)
    temp["period_idx"] = temp["period_label"].map(period_idx)
    temp["sport_grouped"] = pd.Categorical(temp["sport_grouped"], categories=sports, ordered=True)

    y_labels = {
        "distance_km": "km",
        "moving_time_h": "h",
        "elevation_m": "m",
        "activities": "attività",
    }
    unit = y_labels.get(value_col, "")
    color_map = sport_color_map(sports)
    fig = px.bar(
        temp.sort_values(["period_sort", "sport_grouped"]),
        x="period_idx",
        y="value",
        color="sport_grouped",
        barmode="stack",
        color_discrete_map=color_map,
        labels={"period_idx": "", "value": unit, "sport_grouped": ""},
        custom_data=["period_label", "sport_grouped"],
    )
    fig.update_traces(
        marker_line_width=0,
        opacity=0.92,
        width=0.30,
        hovertemplate=f"%{{customdata[0]}}<br>%{{customdata[1]}}<br>%{{y:.1f}} {unit}<extra></extra>",
        showlegend=False,
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(period_order))),
        ticktext=period_order,
        tickangle=0,
        tickfont=dict(size=9, color="#AFC0D2"),
        fixedrange=True,
        showticklabels=False,
        range=[-0.5, max(0.5, len(period_order) - 0.5)],
    )
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(
        bargap=0.60,
        bargroupgap=0.06,
        showlegend=False,
    )
    fig = plot_style(fig, height=120, show_legend=False)
    fig.update_layout(margin=dict(l=48, r=12, t=0, b=0))
    fig.update_yaxes(title_standoff=8, ticklabelposition="outside", automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


def monthly_distance_chart(monthly_sport_df: pd.DataFrame) -> go.Figure:
    return period_metric_chart(monthly_sport_df, value_col="distance_km")

def sport_donut_chart(sport_summary_df: pd.DataFrame) -> go.Figure:
    temp = sport_summary_df.copy()
    if temp.empty:
        return go.Figure()

    temp = temp.sort_values("distance_km", ascending=False).reset_index(drop=True)
    total = float(temp["distance_km"].sum()) or 1.0
    temp["pct"] = temp["distance_km"] / total * 100.0
    color_map = sport_color_map(temp["sport_grouped"].dropna().unique())

    fig = px.pie(
        temp,
        names="sport_grouped",
        values="distance_km",
        hole=0.70,
        color="sport_grouped",
        color_discrete_map=color_map,
    )
    fig.update_traces(
        domain={"x": [0.00, 0.50], "y": [0.06, 0.94]},
        textinfo="none",
        texttemplate=None,
        textposition="none",
        marker=dict(line=dict(color=PANEL, width=1)),
        hovertemplate="%{label}<br>%{value:.1f} km<br>%{percent}<extra></extra>",
        showlegend=False,
    )

    annotations = [
        dict(
            text=f"<b>{total:,.1f}</b><br><span style='font-size:10px'>km totali</span>",
            x=0.25,
            y=0.50,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color=TEXT),
            align="center",
            xanchor="center",
            yanchor="middle",
        )
    ]

    max_rows = min(6, len(temp))
    start_y = 0.74
    step = 0.128 if max_rows <= 5 else 0.108
    for i, row in temp.head(max_rows).iterrows():
        y = start_y - i * step
        sport = str(row["sport_grouped"])
        color = color_map.get(sport, MUTED)
        annotations.extend([
            dict(
                text="●",
                x=0.555,
                y=y,
                xref="paper",
                yref="paper",
                showarrow=False,
                xanchor="center",
                yanchor="middle",
                font=dict(size=14, color=color),
            ),
            dict(
                text=sport,
                x=0.600,
                y=y,
                xref="paper",
                yref="paper",
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(size=7, color=TEXT),
            ),
            dict(
                text=f"{row['pct']:.1f}%",
                x=0.995,
                y=y,
                xref="paper",
                yref="paper",
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font=dict(size=8, color=TEXT),
            ),
        ])

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=annotations,
    )
    return plot_style(fig, height=230, show_legend=False)

def cumulative_trend_chart(cumulative_metric_df: pd.DataFrame, current_year: int) -> go.Figure:
    temp = cumulative_metric_df.copy()
    temp["year_str"] = temp["year"].astype(str)
    temp["month_label"] = pd.Categorical(temp["month_label"], categories=MONTH_ORDER, ordered=True)
    color_map = {str(y): "rgba(125,183,255,0.62)" for y in temp["year"].dropna().unique()}
    color_map[str(current_year)] = "#F05A22"
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
    fig.update_traces(line=dict(width=2.1), marker=dict(size=4.2), hovertemplate="%{x}<br>%{y:.1f}<extra></extra>")
    for trace in fig.data:
        if str(getattr(trace, "name", "")) != str(current_year):
            trace.update(line=dict(dash="dash", width=2.0))
    return plot_style(fig, height=168)


def monthly_trend_chart(trend_metric_df: pd.DataFrame, selected_metric: str, current_year: int) -> go.Figure:
    temp = trend_metric_df.copy().sort_values(["year", "month_num"])
    temp["month"] = pd.Categorical(temp["month"], categories=MONTH_ORDER, ordered=True)
    if temp["year"].nunique() > 1:
        temp["year_str"] = temp["year"].astype(str)
        color_map = {str(y): "rgba(125,183,255,0.62)" for y in temp["year"].dropna().unique()}
        color_map[str(current_year)] = "#F05A22"
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
    fig.update_traces(marker=dict(size=4.8), hovertemplate="%{x}<br>%{y:.1f}<extra></extra>")
    return plot_style(fig, height=238)


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
    return plot_style(fig, height=265, show_legend=False)


def buckets_chart(buckets: pd.DataFrame) -> go.Figure:
    fig = px.bar(buckets, x="bucket", y="count", labels={"bucket": "", "count": "attività"})
    fig.update_traces(marker_color=ACCENT, marker_line_width=0, hovertemplate="%{x}<br>%{y} attività<extra></extra>")
    fig.update_layout(bargap=0.46)
    return plot_style(fig, height=250, show_legend=False)


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
    return plot_style(fig, height=250, show_legend=False)


def progress_gauge(progress: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=progress,
            number={"suffix": "%", "font": {"size": 28, "color": TEXT}},
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
    return plot_style(fig, height=200, show_legend=False)


def zones_pie_chart(zones: pd.DataFrame) -> go.Figure:
    zone_colors = {
        "Zona 1 (Recupero)": "#60A5FA",
        "Zona 2 (Endurance)": "#4ADE80",
        "Zona 3 (Tempo)": "#F59E0B",
        "Zona 4 (Soglia)": "#F97316",
        "Zona 5 (VO2 Max)": "#EF4444",
    }
    fig = px.pie(zones, names="zone", values="activities", hole=0.68, color="zone", color_discrete_map=zone_colors)
    fig.update_traces(textinfo="percent", marker=dict(line=dict(color=PANEL, width=1)), hovertemplate="%{label}<br>%{value} attività<br>%{percent}<extra></extra>")
    return plot_style(fig, height=240)


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
    return plot_style(fig, height=240, show_legend=False)


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
    return plot_style(fig, height=215, show_legend=False)
