from __future__ import annotations

import html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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


PANEL_HEIGHT = 345

TREND_METRICS = {
    "Distanza": ("distance_km", "km"),
    "Tempo": ("moving_time_h", "h"),
    "Dislivello": ("elevation_m", "m"),
    "Attività": ("activities", "attività"),
}
TREND_VIEWS = ["Mensile", "Settimanale"]


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
    preferred = ["Ciclismo", "Ride", "VirtualRide", "GravelRide", "Corsa", "Run", "Escursionismo", "Hike", "Altri"]
    sports = [s for s in preferred if s in available] + [s for s in available if s not in preferred]
    color_map = sport_color_map(sports)
    items = "".join(
        f"<span class='sd-card-legend-item'><span class='sd-card-dot' style='background:{color_map.get(sport, '#94A3B8')}'></span>{_esc(sport)}</span>"
        for sport in sports
    )
    return f"<div class='sd-card-legend'>{items}</div>"


def _month_axis_labels_html(df) -> str:
    if df.empty or not {"year", "month_num"}.issubset(df.columns):
        return ""

    temp = df[["year", "month_num"]].dropna().drop_duplicates().copy()
    if temp.empty:
        return ""

    temp["year"] = temp["year"].astype(int)
    temp["month_num"] = temp["month_num"].astype(int)

    month_names = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    min_year = int(temp["year"].min())
    max_year = int(temp["year"].max())
    max_month = int(temp.loc[temp["year"] == max_year, "month_num"].max())

    labels: list[str] = []
    for year in range(min_year, max_year + 1):
        end_month = 12 if year < max_year else max_month
        for month_num in range(1, end_month + 1):
            labels.append(f"<span>{month_names[month_num - 1]}<br>{year}</span>")

    cols = max(1, len(labels))
    return f"<div class='sd-custom-xaxis' style='grid-template-columns: repeat({cols}, minmax(0, 1fr));'>" + "".join(labels) + "</div>"



def _period_axis_labels_html(labels: list[str]) -> str:
    if not labels:
        return ""
    cols = max(1, len(labels))
    items = "".join(f"<span>{label}</span>" for label in labels)
    return f"<div class='sd-custom-xaxis' style='grid-template-columns: repeat({cols}, minmax(0, 1fr));'>{items}</div>"


def _weekly_by_sport_from_data(data: dict, fallback_monthly: pd.DataFrame) -> pd.DataFrame:
    df = _activity_dataframe_from_data(data)
    if df is None or df.empty:
        return pd.DataFrame()

    temp = df.copy()
    if "sport_grouped" not in temp.columns:
        if "sport_label" in temp.columns:
            temp["sport_grouped"] = temp["sport_label"]
        else:
            return pd.DataFrame()

    if "week" not in temp.columns or "year" not in temp.columns:
        date_col = None
        for candidate in ("start_date_local", "start_date", "day"):
            if candidate in temp.columns:
                date_col = candidate
                break
        if date_col is None:
            return pd.DataFrame()
        dates = pd.to_datetime(temp[date_col], errors="coerce")
        temp["year"] = dates.dt.year
        temp["week"] = dates.dt.isocalendar().week.astype("Int64")

    for col in ("distance_km", "moving_time_h", "elevation_m"):
        if col not in temp.columns:
            temp[col] = 0.0
    if "id" not in temp.columns:
        temp["id"] = range(1, len(temp) + 1)

    out = (
        temp.dropna(subset=["year", "week"])
        .groupby(["year", "week", "sport_grouped"], as_index=False, dropna=False)
        .agg(
            distance_km=("distance_km", "sum"),
            moving_time_h=("moving_time_h", "sum"),
            elevation_m=("elevation_m", "sum"),
            activities=("id", "count"),
        )
        .sort_values(["year", "week"])
    )
    return out


def _period_bar_chart(period_df: pd.DataFrame, metric_col: str, view: str) -> tuple[go.Figure, list[str], int]:
    temp = period_df.copy()
    if temp.empty:
        return go.Figure(), [], 640

    if metric_col not in temp.columns:
        temp[metric_col] = 0.0

    preferred = ["Ciclismo", "Ride", "VirtualRide", "GravelRide", "Corsa", "Run", "Escursionismo", "Hike", "Altri"]
    available = [str(x) for x in temp["sport_grouped"].dropna().unique().tolist()]
    sports = [sport for sport in preferred if sport in available] + [sport for sport in available if sport not in preferred]
    color_map = sport_color_map(sports)

    if view == "Settimanale" and {"year", "week"}.issubset(temp.columns):
        temp = temp.dropna(subset=["year", "week"]).copy()
        if temp.empty:
            return go.Figure(), [], 640
        temp["year"] = temp["year"].astype(int)
        temp["week"] = temp["week"].astype(int)
        periods_df = temp[["year", "week"]].drop_duplicates().sort_values(["year", "week"]).reset_index(drop=True)
        periods_df["period_label"] = periods_df.apply(lambda r: f"W{int(r['week']):02d}<br>{int(r['year'])}", axis=1)
        join_cols = ["year", "week"]
        sort_cols = ["year", "week", "sport_grouped"]
        min_width = max(680, int(len(periods_df) * 30))
    else:
        temp = temp.dropna(subset=["year", "month_num"]).copy()
        if temp.empty:
            return go.Figure(), [], 640
        temp["year"] = temp["year"].astype(int)
        temp["month_num"] = temp["month_num"].astype(int)
        month_names = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        min_year = int(temp["year"].min())
        max_year = int(temp["year"].max())
        max_month = int(temp.loc[temp["year"] == max_year, "month_num"].max())
        rows = []
        for year in range(min_year, max_year + 1):
            end_month = 12 if year < max_year else max_month
            for month_num in range(1, end_month + 1):
                rows.append({"year": year, "month_num": month_num, "period_label": f"{month_names[month_num - 1]}<br>{year}"})
        periods_df = pd.DataFrame(rows)
        join_cols = ["year", "month_num"]
        sort_cols = ["year", "month_num", "sport_grouped"]
        min_width = max(640, int(len(periods_df) * 44))

    if periods_df.empty or not sports:
        return go.Figure(), [], min_width

    full_index = periods_df[join_cols + ["period_label"]].merge(pd.DataFrame({"sport_grouped": sports}), how="cross")
    temp = full_index.merge(temp, on=join_cols + ["sport_grouped"], how="left")
    temp[metric_col] = pd.to_numeric(temp[metric_col], errors="coerce").fillna(0.0)
    period_order = periods_df["period_label"].astype(str).tolist()
    period_idx = {label: i for i, label in enumerate(period_order)}
    temp["period_label"] = temp["period_label"].astype(str)
    temp["period_idx"] = temp["period_label"].map(period_idx)
    temp["sport_grouped"] = pd.Categorical(temp["sport_grouped"], categories=sports, ordered=True)

    unit = next((unit for _label, (col, unit) in TREND_METRICS.items() if col == metric_col), "")
    fig = px.bar(
        temp.sort_values(sort_cols),
        x="period_idx",
        y=metric_col,
        color="sport_grouped",
        barmode="stack",
        color_discrete_map=color_map,
        labels={"period_idx": "", metric_col: unit, "sport_grouped": ""},
        custom_data=["period_label", "sport_grouped"],
    )
    fig.update_traces(
        marker_line_width=0,
        opacity=0.92,
        width=0.42 if view == "Mensile" else 0.58,
        hovertemplate=f"%{{customdata[0]}}<br>%{{customdata[1]}}<br>%{{y:.1f}} {unit}<extra></extra>",
        showlegend=False,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(period_order))),
        ticktext=period_order,
        showticklabels=False,
        fixedrange=True,
        range=[-0.5, max(0.5, len(period_order) - 0.5)],
    )
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(bargap=0.40 if view == "Mensile" else 0.24, bargroupgap=0.08, showlegend=False)
    from app.charts import plot_style
    fig = plot_style(fig, height=130, show_legend=False)
    fig.update_layout(margin=dict(l=48, r=12, t=0, b=0))
    fig.update_yaxes(title_standoff=8, ticklabelposition="outside", automargin=True)
    fig.update_xaxes(automargin=True)
    return fig, period_order, min_width

def _plotly_fragment(fig, height: int) -> str:
    return fig.to_html(
        include_plotlyjs="cdn",
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
        default_width="100%",
        default_height=f"{height}px",
    )


def _render_monthly_card(
    chart_variants: dict[tuple[str, str], tuple[go.Figure, list[str], int]],
    legend_html: str,
    height: int = PANEL_HEIGHT,
) -> None:
    chart_height = 130
    chart_blocks: list[str] = []
    metric_options = list(TREND_METRICS.keys())
    view_options = TREND_VIEWS

    for metric_label in metric_options:
        for view_label in view_options:
            fig, labels, min_width = chart_variants.get((metric_label, view_label), (go.Figure(), [], 640))
            html_fragment = _plotly_fragment(fig, chart_height)
            axis_labels_html = _period_axis_labels_html(labels)
            active = " is-active" if metric_label == "Distanza" and view_label == "Mensile" else ""
            chart_blocks.append(
                '<div class="sd-chart-variant{}" data-metric="{}" data-view="{}">'
                '<div class="sd-scroll-shell"><div class="sd-scroll-inner" style="min-width:{}px;">{}{}</div></div></div>'.format(
                    active,
                    _esc(metric_label),
                    _esc(view_label),
                    min_width,
                    html_fragment,
                    axis_labels_html,
                )
            )

    metric_options_html = "".join(
        f"<option value='{_esc(label)}' {'selected' if label == 'Distanza' else ''}>{_esc(label)}</option>"
        for label in metric_options
    )
    view_options_html = "".join(
        f"<option value='{_esc(label)}' {'selected' if label == 'Mensile' else ''}>{_esc(label)}</option>"
        for label in view_options
    )

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
                padding: 18px 24px 12px 24px;
                overflow: hidden;
                color: #F7FAFF;
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            }}
            .sd-card-top {{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px;}}
            .sd-card-title {{font-size: 1.03rem; font-weight: 850; letter-spacing: -0.035em; margin: 18px 0 0 0; white-space:nowrap;min-width:0;}}
            .sd-control-row {{display:flex;align-items:flex-end;gap:8px;justify-content:flex-end;flex:0 0 auto;}}
            .sd-control {{width:110px;position:relative;}}
            .sd-control.small {{width:104px;}}
            .sd-control-label {{font-size:.52rem;letter-spacing:.08em;text-transform:uppercase;color:#AFC0D2;font-weight:820;margin-bottom:4px;white-space:nowrap;}}
            .sd-native-select {{
                width:100%;height:30px;border-radius:11px;border:1px solid rgba(216,230,255,.12);
                background:#0A1626;color:#F7FAFF;padding:0 24px 0 9px;font-size:.68rem;font-weight:760;
                box-sizing:border-box;outline:none;cursor:pointer;appearance:auto;-webkit-appearance:menulist;
            }}
            .sd-native-select:focus {{border-color:rgba(252,76,2,.55);box-shadow:0 0 0 2px rgba(252,76,2,.10);}}
            .sd-card-panel .sd-card-legend {{display:flex !important;flex-wrap:wrap;gap:9px 14px;align-items:center;margin:0 0 7px 0;font-size:.72rem;color:#EAF2FF;line-height:1.15;}}
            .sd-card-panel .sd-card-legend-item {{display:inline-flex !important;align-items:center;gap:7px;white-space:nowrap;font-weight:720;}}
            .sd-card-panel .sd-card-dot {{width:9px;height:9px;min-width:9px;border-radius:50%;display:inline-block;box-shadow:0 0 0 2px rgba(255,255,255,0.035);}}
            .sd-chart-variant {{display:none;}}
            .sd-chart-variant.is-active {{display:block;}}
            .sd-scroll-shell {{
                width: 100%;height: 186px;overflow-x: auto;overflow-y: hidden;padding-bottom: 12px;box-sizing: border-box;
                scrollbar-width: thin;scrollbar-color: rgba(226,232,240,0.82) rgba(255,255,255,0.10);
            }}
            .sd-scroll-shell::-webkit-scrollbar {{height: 9px;}}
            .sd-scroll-shell::-webkit-scrollbar-track {{background: rgba(255,255,255,0.10); border-radius: 999px;}}
            .sd-scroll-shell::-webkit-scrollbar-thumb {{background: rgba(226,232,240,0.82); border-radius: 999px;}}
            .sd-scroll-inner {{height: {chart_height + 46}px;}}
            .sd-custom-xaxis {{
                display:grid;margin-left:48px;margin-right:12px;margin-top:-2px;color:#AFC0D2;font-size:8.5px;
                line-height: 1.15;text-align: center;white-space: normal;
            }}
        </style>
        <div class="sd-card-panel">
            <div class="sd-card-top">
                <div class="sd-card-title" id="sd-trend-title">Andamento mensile</div>
                <div class="sd-control-row">
                    <div class="sd-control">
                        <div class="sd-control-label">Metrica</div>
                        <select class="sd-native-select" id="sd-metric-select" aria-label="Metrica trend">{metric_options_html}</select>
                    </div>
                    <div class="sd-control small">
                        <div class="sd-control-label">Vista</div>
                        <select class="sd-native-select" id="sd-view-select" aria-label="Vista trend">{view_options_html}</select>
                    </div>
                </div>
            </div>
            {legend_html}
            {''.join(chart_blocks)}
        </div>
        <script>
        (function() {{
            const root = document.currentScript.previousElementSibling;
            const metricSelect = root.querySelector('#sd-metric-select');
            const viewSelect = root.querySelector('#sd-view-select');
            const title = root.querySelector('#sd-trend-title');
            function setActive() {{
                const metric = metricSelect.value;
                const view = viewSelect.value;
                if (title) title.textContent = view === 'Settimanale' ? 'Andamento settimanale' : 'Andamento mensile';
                root.querySelectorAll('.sd-chart-variant').forEach(el => {{
                    el.classList.toggle('is-active', el.dataset.metric === metric && el.dataset.view === view);
                }});
            }}
            metricSelect.addEventListener('change', setActive);
            viewSelect.addEventListener('change', setActive);
            setActive();
        }})();
        </script>
        """,
        height=height,
        scrolling=False,
    )


def _render_donut_card(fig, height: int = PANEL_HEIGHT) -> None:
    chart_height = 230
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
                padding: 20px 24px 13px 24px;
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
    streak = kpis.get("weekly_streak", None)
    if streak is None:
        streak = _current_training_week_streak(data)
    streak_value = "-" if streak is None else str(int(streak))
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




ANNUAL_DISTANCE_TARGETS_KM = {
    "Ciclismo": 4055.0,
    "VirtualRide": 870.0,
    "Corsa": 45.0,
    "Escursionismo": 30.0,
}


def _annual_goal_values(data: dict, kpis: dict) -> tuple[float, float, float]:
    """Return current distance, fixed annual target and progress percentage.

    The annual target is intentionally fixed for the whole year and split by
    the current sport mix selected by the user:
    Ciclismo 4,055 km, VirtualRide 870 km, Corsa 45 km, Escursionismo 30 km.
    This avoids a moving target and avoids using the previous year as baseline.
    """
    current_km = float(kpis.get("distance_km", 0.0) or 0.0)
    target_km = float(sum(ANNUAL_DISTANCE_TARGETS_KM.values()))
    progress_pct = min(100.0, (current_km / target_km) * 100.0) if target_km > 0 else 0.0
    return current_km, target_km, progress_pct


def _render_cumulative_card(fig, delta_pct: float, previous_year: int, height: int = 258) -> None:
    chart_height = 168
    trend_badge_class = "positive" if delta_pct >= 0 else "negative"
    fig.update_layout(
        height=chart_height,
        margin=dict(l=34, r=12, t=8, b=22),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0.02),
    )
    fig.update_xaxes(automargin=True, tickfont=dict(size=8))
    fig.update_yaxes(automargin=True, tickfont=dict(size=8))
    html_fragment = _plotly_fragment(fig, chart_height)
    components.html(
        f'''
        <style>
            .sd-bottom-card {{
                height: {height}px;
                box-sizing: border-box;
                border: 1px solid rgba(216,230,255,0.105);
                border-radius: 16px;
                background: radial-gradient(circle at 20% 0%, rgba(125,183,255,0.052), transparent 16rem), rgba(10,20,34,0.86);
                padding: 14px 16px 12px;
                overflow: hidden;
                color: #F7FAFF;
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
            }}
            .sd-bottom-title {{font-size:.82rem;font-weight:860;text-transform:uppercase;letter-spacing:.02em;margin:0 0 5px;}}
            .sd-bottom-sub {{font-size:.70rem;color:#AFC0D2;margin-bottom:5px;}}
            .sd-trend-chart {{height:{chart_height}px;margin-top:2px;}}
            .sd-trend-badge {{
                display:inline-flex;align-items:center;
                border-radius:10px;padding:6px 9px;font-weight:760;font-size:.68rem;margin-top:0;
            }}
            .sd-trend-badge.positive {{border:1px solid rgba(34,197,94,.48);color:#BBF7D0;background:rgba(34,197,94,.10);}}
            .sd-trend-badge.negative {{border:1px solid rgba(239,68,68,.48);color:#FECACA;background:rgba(239,68,68,.10);}}
            .sd-trend-badge.positive b {{color:#86EFAC;margin-right:4px;}}
            .sd-trend-badge.negative b {{color:#FDA4AF;margin-right:4px;}}
        </style>
        <div class="sd-bottom-card">
            <div class="sd-bottom-title">Trend vs anno scorso</div>
            <div class="sd-bottom-sub">Confronto cumulativo progressivo</div>
            <div class="sd-trend-chart">{html_fragment}</div>
            <div class="sd-trend-badge {trend_badge_class}"><b>{fmt_pct(delta_pct)}</b> rispetto al {previous_year}</div>
        </div>
        ''',
        height=height,
        scrolling=False,
    )


def _performance_card_html(bp: pd.DataFrame, height: int = 258) -> str:
    if bp.empty:
        body = "<div class='big-empty'>Nessun dato disponibile.</div>"
    else:
        icon_map = ["🚴", "👟", "⛰️", "🕘"]
        rows: list[str] = []
        for idx, row in enumerate(bp.head(4).to_dict("records")):
            rows.append(
                "<div class='sd-perf-row'>"
                f"<div class='sd-perf-icon'>{icon_map[idx % len(icon_map)]}</div>"
                "<div class='sd-perf-copy'>"
                f"<div class='sd-perf-value'>{_esc(row.get('value', '-'))}</div>"
                f"<div class='sd-perf-sub'>{_esc(row.get('date', '-'))}</div>"
                "</div>"
                f"<div class='sd-perf-label'>{_esc(row.get('label', 'Performance'))}</div>"
                "</div>"
            )
        body = "".join(rows)
    return f'''
    <div class="sd-bottom-html-card" style="height:{height}px;">
        <div class="sd-bottom-html-head">
            <h3>Migliori performance</h3>
            <p>Record e attività più rilevanti</p>
        </div>
        <div class="sd-bottom-html-body">{body}</div>
    </div>
    '''


def _zones_card_html(zones: pd.DataFrame, height: int = 258) -> str:
    if zones.empty:
        body = "<div class='big-empty'>Nessun dato disponibile.</div>"
    else:
        colors = ["#3B82F6", "#4ADE80", "#FBBF24", "#FB923C", "#EF4444"]
        rows: list[str] = []
        for idx, (_, row) in enumerate(zones.head(5).iterrows()):
            zone = _esc(row.get("zone", "Zona"))
            activities = float(row.get("activities_pct", 0.0) or 0.0)
            width = max(2.0, min(100.0, activities))
            color = colors[idx % len(colors)]
            rows.append(
                "<div class='sd-zone-v2-row'>"
                f"<div class='sd-zone-v2-label'>{zone}</div>"
                "<div class='sd-zone-v2-track'>"
                f"<div class='sd-zone-v2-fill' style='width:{width:.1f}%;background:{color};'></div>"
                "</div>"
                f"<div class='sd-zone-v2-num'>{activities:.0f}%</div>"
                "</div>"
            )
        body = "".join(rows)
    return f'''
    <div class="sd-bottom-html-card" style="height:{height}px;">
        <div class="sd-bottom-html-head compact">
            <h3>Zone di frequenza <span>(attività)</span></h3>
        </div>
        <div class="sd-bottom-html-body">{body}</div>
    </div>
    '''


def _mini_bottom_kpi_html(icon: str, klass: str, title: str, value: str, subtitle: str) -> str:
    return f'''
    <div class="sd-bottom-kpi">
        <div class="sd-bottom-kpi-icon {klass}">{icon}</div>
        <div class="sd-bottom-kpi-copy">
            <div class="sd-bottom-kpi-label">{_esc(title)}</div>
            <div class="sd-bottom-kpi-value">{_esc(value)}</div>
            <div class="sd-bottom-kpi-sub">{_esc(subtitle)}</div>
        </div>
    </div>
    '''

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
            font-size: .72rem;
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
            padding: 13px 13px 10px;
            height: 345px;
            min-height: 345px;
            box-sizing: border-box;
        }
        .sd-key-title {
            color: #F7FAFF;
            font-size: .72rem;
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
            grid-template-columns: 36px minmax(0, 1fr);
            column-gap: 10px;
            align-items: center;
            min-height: 58px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(216,230,255,0.075);
        }
        .sd-key-row:last-child { border-bottom: 0; }
        .sd-key-icon {
            width: 32px;
            height: 32px;
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
            font-size: 1.00rem;
            font-weight: 860;
            letter-spacing: -0.035em;
            line-height: 1.05;
        }
        .sd-key-label {
            color: #D8E6F6;
            font-size: .72rem;
            line-height: 1.15;
            margin-top: 2px;
        }
        .sd-key-sub {
            color: #AFC0D2;
            font-size: .64rem;
            line-height: 1.15;
            margin-top: 2px;
        }


        .sd-bottom-html-card {
            border: 1px solid rgba(216,230,255,0.105); border-radius: 16px;
            background: radial-gradient(circle at 20% 0%, rgba(125,183,255,0.052), transparent 16rem), rgba(10,20,34,0.86);
            padding: 14px 16px 12px; box-sizing: border-box; overflow: hidden; color: #F7FAFF;
        }
        .sd-bottom-html-head h3 { margin: 0; color: #F7FAFF; font-size: .82rem; font-weight: 860; text-transform: uppercase; letter-spacing: .02em; }
        .sd-bottom-html-head h3 span { color: #AFC0D2; font-weight: 640; text-transform: none; letter-spacing: 0; }
        .sd-bottom-html-head p { margin: 6px 0 10px; color: #AFC0D2; font-size: .70rem; }
        .sd-bottom-html-head.compact { margin-bottom: 16px; }
        .sd-perf-row { display: grid; grid-template-columns: 38px minmax(0, .84fr) minmax(0, 1fr); align-items: center; gap: 10px; border: 1px solid rgba(216,230,255,0.085); border-radius: 10px; background: rgba(7,16,28,0.36); min-height: 41px; padding: 6px 8px; margin-bottom: 6px; }
        .sd-perf-icon { width: 30px; height: 30px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(252,76,2,0.12); font-size: 1rem; }
        .sd-perf-value { color: #F7FAFF; font-size: .88rem; font-weight: 850; letter-spacing: -.02em; line-height: 1.05; }
        .sd-perf-sub { color: #AFC0D2; font-size: .62rem; margin-top: 2px; }
        .sd-perf-label { color: #D8E6F6; font-size: .66rem; line-height: 1.18; text-align: right; }
        .sd-zone-v2-row { display: grid; grid-template-columns: minmax(96px, .72fr) minmax(80px, 1fr) 36px; gap: 10px; align-items: center; margin-bottom: 13px; }
        .sd-zone-v2-label { color: #D8E6F6; font-size: .68rem; line-height: 1.1; }
        .sd-zone-v2-track { height: 7px; border-radius: 999px; background: rgba(255,255,255,0.08); overflow: hidden; }
        .sd-zone-v2-fill { height: 100%; border-radius: 999px; box-shadow: 8px 0 0 rgba(255,255,255,0.18); }
        .sd-zone-v2-num { color: #F7FAFF; font-size: .72rem; font-weight: 760; text-align: right; }
        .sd-bottom-kpi { min-height: 64px; border: 1px solid rgba(216,230,255,0.105); border-radius: 14px; background: radial-gradient(circle at 20% 0%, rgba(125,183,255,0.05), transparent 14rem), rgba(10,20,34,0.82); padding: 12px 14px; display: grid; grid-template-columns: 38px minmax(0, 1fr); gap: 12px; align-items: center; }
        .sd-bottom-kpi-icon { width: 34px; height: 34px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.08rem; }
        .sd-bottom-kpi-icon.calendar { background: rgba(14,165,233,0.14); color: #38BDF8; }
        .sd-bottom-kpi-icon.week { background: rgba(34,197,94,0.14); color: #4ADE80; }
        .sd-bottom-kpi-icon.sport { background: rgba(34,197,94,0.14); color: #4ADE80; }
        .sd-bottom-kpi-icon.goal { background: rgba(239,68,68,0.14); color: #F87171; }
        .sd-bottom-kpi-label { color: #AFC0D2; font-size: .62rem; line-height: 1; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; }
        .sd-bottom-kpi-value { color: #F7FAFF; font-size: .95rem; font-weight: 850; margin-top: 5px; letter-spacing: -.025em; }
        .sd-bottom-kpi-sub { color: #D8E6F6; font-size: .68rem; margin-top: 2px; }
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
    # ROW 1: Monthly trend + sport distribution + key numbers
    # =====================================================
    left, middle, right = st.columns([1.64, 1.24, 0.82], gap="small")

    with left:
        if monthly_sport_df.empty:
            _empty()
        else:
            legend_html = _sport_legend_html(monthly_sport_df)
            weekly_sport_df = _weekly_by_sport_from_data(data, monthly_sport_df)
            chart_variants = {}
            for metric_label, (metric_col, _unit) in TREND_METRICS.items():
                chart_variants[(metric_label, "Mensile")] = _period_bar_chart(monthly_sport_df, metric_col, "Mensile")
                chart_variants[(metric_label, "Settimanale")] = (
                    chart_variants[(metric_label, "Mensile")]
                    if weekly_sport_df.empty
                    else _period_bar_chart(weekly_sport_df, metric_col, "Settimanale")
                )
            _render_monthly_card(chart_variants, legend_html, height=PANEL_HEIGHT)

    with middle:
        if sport_summary_df.empty:
            _empty()
        else:
            _render_donut_card(sport_donut_chart(sport_summary_df), height=PANEL_HEIGHT)

    with right:
        st.markdown(_key_numbers_html(data, kpis), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # =====================================================
    # ROW 2: trend + performance + zones aligned
    # =====================================================
    bottom_height = 258
    r2_c1, r2_c2, r2_c3 = st.columns([1.64, 0.92, 1.14], gap="small")

    with r2_c1:
        if cumulative_metric_df.empty:
            st.markdown(_compact_overview_card("Trend vs anno scorso", "Confronto cumulativo progressivo", "<div class='big-empty'>Nessun confronto disponibile.</div>", height=bottom_height), unsafe_allow_html=True)
        else:
            _render_cumulative_card(
                cumulative_trend_chart(cumulative_metric_df, distance_compare["current_year"]),
                distance_compare["delta_pct"],
                distance_compare["previous_year"],
                height=bottom_height,
            )

    with r2_c2:
        st.markdown(_performance_card_html(bp, height=bottom_height), unsafe_allow_html=True)

    with r2_c3:
        st.markdown(_zones_card_html(zones, height=bottom_height), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # =====================================================
    # ROW 3: secondary KPI boxes
    # =====================================================
    current_km, target_km, goal_pct = _annual_goal_values(data, kpis)
    k1, k2, k3, k4 = st.columns(4, gap="small")

    with k1:
        st.markdown(_mini_bottom_kpi_html("🚴", "sport", "Sport principale", str(main_sport.get("sport", "-")), f"{main_sport.get('pct', 0):.0f}% della distanza"), unsafe_allow_html=True)
    with k2:
        st.markdown(_mini_bottom_kpi_html("📅", "calendar", "Giorno preferito", str(fav_day.get("weekday", "-")), f"{fav_day.get('pct', 0):.0f}% delle attività"), unsafe_allow_html=True)
    with k3:
        st.markdown(_mini_bottom_kpi_html("📈", "week", "Settimana top", str(active_week.get("week", "-")), f"{active_week.get('activities', 0)} attività"), unsafe_allow_html=True)
    with k4:
        st.markdown(_mini_bottom_kpi_html("🎯", "goal", "Obiettivo annuale", f"{goal_pct:.0f}%", f"{fmt_km(current_km)} / {fmt_km(target_km)}"), unsafe_allow_html=True)
