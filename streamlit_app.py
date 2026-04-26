from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.config import get_settings, iso_to_unix
from app.metrics import (
    normalize_activities,
    filter_activities,
    available_sports,
    kpi_summary,
    summary_by_sport,
    monthly_by_sport,
    cumulative_by_year,
    trend_monthly,
    compare_vs_previous_year,
    best_performances,
    favorite_weekday,
    group_small_sports,
    most_active_week,
    primary_sport,
    distance_bucket_distribution,
    personal_records,
    zone_proxy,
    monthly_best_worst,
    consistency_score,
)
from app.storage import load_activities, save_activities
from app.strava_api import StravaClient


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Strava Dashboard",
    page_icon="🚴",
    layout="wide",
)


# ============================================================
# THEME / STYLE
# ============================================================

SPORT_COLORS = {
    "Ciclismo": "#ff7a1a",
    "VirtualRide": "#3b82f6",
    "Corsa": "#ff4d4f",
    "Escursionismo": "#4ade80",
    "GravelRide": "#8b5cf6",
    "Altri": "#64748b",
}

SPORT_ICONS = {
    "Ciclismo": "🚴",
    "VirtualRide": "💻",
    "Corsa": "👟",
    "Escursionismo": "🥾",
    "GravelRide": "🪨",
    "Altri": "✨",
}

BG = "#07111f"
PANEL = "#0b1830"
PANEL_2 = "#0f1d38"
BORDER = "rgba(148, 163, 184, 0.18)"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
ACCENT = "#ff7a1a"
GREEN = "#22c55e"
RED = "#ef4444"

st.markdown(
    f"""
    <style>
    .stApp {{
        background:
            radial-gradient(circle at top right, rgba(25, 55, 95, 0.45), transparent 28%),
            linear-gradient(180deg, #07111f 0%, #09162a 100%);
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1450px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }}

    h1, h2, h3, h4, h5, h6, p, div, span, label {{
        color: {TEXT};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stToolbar"] {{
        right: 0.5rem;
    }}

    .app-title {{
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.4rem;
        letter-spacing: -0.03em;
    }}

    .app-subtitle {{
        color: {MUTED};
        font-size: 1rem;
        margin-bottom: 1.25rem;
    }}

    .hero-wrap {{
        background: linear-gradient(180deg, rgba(11,24,48,0.88) 0%, rgba(8,18,35,0.88) 100%);
        border: 1px solid {BORDER};
        border-radius: 22px;
        padding: 20px 20px 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }}

    .filter-wrap {{
        background: linear-gradient(180deg, rgba(11,24,48,0.85) 0%, rgba(8,18,35,0.85) 100%);
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 14px 14px 4px 14px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }}

    .kpi-card {{
        background: linear-gradient(180deg, rgba(13,27,52,1) 0%, rgba(9,22,42,1) 100%);
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 16px 18px 14px 18px;
        min-height: 125px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.16);
    }}

    .kpi-label {{
        font-size: 0.88rem;
        color: #cbd5e1;
        margin-bottom: 10px;
    }}

    .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.05;
        margin-bottom: 8px;
        color: white;
    }}

    .kpi-delta {{
        font-size: 0.9rem;
        color: {GREEN};
        font-weight: 600;
    }}

    .panel {{
        background: linear-gradient(180deg, rgba(11,24,48,0.98) 0%, rgba(8,18,35,0.98) 100%);
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 14px 14px 10px 14px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.16);
        margin-bottom: 14px;
    }}

    .panel-title {{
        font-size: 1.15rem;
        font-weight: 800;
        margin-bottom: 10px;
        color: white;
    }}

    .panel-note {{
        color: {MUTED};
        font-size: 0.9rem;
        margin-top: -2px;
        margin-bottom: 8px;
    }}

    .mini-stat {{
        background: rgba(255,255,255,0.02);
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 14px 14px 10px 14px;
        margin-bottom: 10px;
    }}

    .mini-label {{
        color: {MUTED};
        font-size: 0.85rem;
        margin-bottom: 4px;
    }}

    .mini-value {{
        color: white;
        font-size: 1.55rem;
        font-weight: 800;
        line-height: 1.1;
    }}

    .mini-sub {{
        color: #cbd5e1;
        font-size: 0.9rem;
        margin-top: 4px;
    }}

    .pill {{
        display: inline-block;
        background: rgba(255,122,26,0.10);
        color: #ffb37b;
        border: 1px solid rgba(255,122,26,0.22);
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }}

    .insight-row {{
        padding: 10px 0;
        border-bottom: 1px solid rgba(148,163,184,0.12);
    }}

    .insight-row:last-child {{
        border-bottom: none;
    }}

    .insight-main {{
        font-size: 1.05rem;
        font-weight: 700;
        color: white;
    }}

    .insight-sub {{
        color: {MUTED};
        font-size: 0.88rem;
        margin-top: 2px;
    }}

    .table-wrap {{
        background: transparent;
        overflow-x: auto;
    }}

    .data-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.95rem;
        overflow: hidden;
        border-radius: 14px;
        border: 1px solid {BORDER};
    }}

    .data-table th {{
        background: rgba(255,255,255,0.04);
        color: #cbd5e1;
        text-align: left;
        padding: 12px 14px;
        font-weight: 700;
        border-bottom: 1px solid rgba(148,163,184,0.12);
    }}

    .data-table td {{
        padding: 12px 14px;
        border-bottom: 1px solid rgba(148,163,184,0.08);
        color: white;
    }}

    .data-table tr:last-child td {{
        border-bottom: none;
    }}

    .data-table tr:nth-child(even) td {{
        background: rgba(255,255,255,0.015);
    }}

    .tiny {{
        color: {MUTED};
        font-size: 0.86rem;
    }}

    .big-empty {{
        background: linear-gradient(180deg, rgba(11,24,48,0.9) 0%, rgba(8,18,35,0.9) 100%);
        border: 1px dashed rgba(148,163,184,0.22);
        border-radius: 18px;
        padding: 28px;
        text-align: center;
        color: {MUTED};
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        margin-bottom: 8px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 12px 12px 0 0;
        color: #cbd5e1;
        padding: 8px 8px;
        font-weight: 600;
    }}

    .stTabs [aria-selected="true"] {{
        color: {ACCENT} !important;
    }}

    [data-testid="stExpander"] {{
        background: transparent;
        border: none !important;
    }}

    .stMultiSelect div[data-baseweb="select"] > div,
    .stSelectbox div[data-baseweb="select"] > div,
    .stDateInput > div > div {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 12px;
        color: white;
    }}

    .stButton button {{
        background: linear-gradient(180deg, #ff7a1a 0%, #f97316 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        padding: 0.5rem 1rem;
    }}

    .stButton button:hover {{
        background: linear-gradient(180deg, #ff8b36 0%, #fb7c20 100%);
        color: white;
    }}

    div[data-testid="stMetric"] {{
        background: linear-gradient(180deg, rgba(13,27,52,1) 0%, rgba(9,22,42,1) 100%);
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 12px 16px;
    }}

    div[data-testid="stMetricLabel"] * {{
        color: #cbd5e1 !important;
    }}

    div[data-testid="stMetricValue"] * {{
        color: white !important;
    }}

    div[data-testid="stMetricDelta"] * {{
        color: {GREEN} !important;
    }}

    /* ---------- FIX LEGGIBILITA WIDGET ---------- */

    [data-testid="stExpander"] details summary,
    [data-testid="stExpander"] details summary p,
    [data-testid="stExpander"] details summary span,
    [data-testid="stExpander"] details summary div {{
        color: white !important;
    }}

    .stMultiSelect label,
    .stSelectbox label,
    .stDateInput label,
    .stTextInput label,
    .stNumberInput label {{
        color: #e5e7eb !important;
        font-weight: 600;
    }}

    .stMultiSelect div[data-baseweb="select"] *,
    .stSelectbox div[data-baseweb="select"] *,
    .stDateInput * {{
        color: white !important;
    }}

    div[role="listbox"] {{
        background: #0f1d38 !important;
        color: white !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
    }}

    div[role="option"] {{
        background: #0f1d38 !important;
        color: white !important;
    }}

    div[role="option"]:hover {{
        background: rgba(255, 122, 26, 0.14) !important;
        color: white !important;
    }}

    .stMultiSelect [data-baseweb="tag"] {{
        background: rgba(255, 122, 26, 0.14) !important;
        border: 1px solid rgba(255, 122, 26, 0.26) !important;
        color: white !important;
    }}

    .stMultiSelect [data-baseweb="tag"] * {{
        color: white !important;
    }}

    [data-baseweb="calendar"],
    [data-baseweb="calendar"] * {{
        background: #0f1d38 !important;
        color: white !important;
    }}

    .stDateInput input {{
        color: white !important;
        -webkit-text-fill-color: white !important;
    }}

    input::placeholder,
    textarea::placeholder {{
        color: #94a3b8 !important;
        opacity: 1 !important;
    }}

    @media (max-width: 768px) {{
        .app-title {{
            font-size: 2.3rem;
        }}
        .kpi-value {{
            font-size: 1.7rem;
        }}
        .panel-title {{
            font-size: 1rem;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def fmt_km(v: float) -> str:
    return f"{v:,.1f} km"


def fmt_h(v: float) -> str:
    return f"{v:,.1f} h"


def fmt_m(v: float) -> str:
    return f"{v:,.0f} m"


def fmt_int(v: float) -> str:
    return f"{int(round(v))}"


def fmt_pct(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.0f}%"


def sport_color_map(labels: Iterable[str]) -> dict[str, str]:
    return {lab: SPORT_COLORS.get(lab, SPORT_COLORS["Other"]) for lab in labels}


def card_html(label: str, value: str, delta: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta">{delta if delta else "&nbsp;"}</div>
    </div>
    """


def mini_stat_html(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class="mini-stat">
        <div class="mini-label">{label}</div>
        <div class="mini-value">{value}</div>
        <div class="mini-sub">{sub}</div>
    </div>
    """


def section_open(title: str, note: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{title}</div>
            {f'<div class="panel-note">{note}</div>' if note else ''}
        """,
        unsafe_allow_html=True,
    )


def section_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_html_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        return
    html = df.to_html(index=False, classes="data-table", border=0, escape=False)
    st.markdown(f"<div class='table-wrap'>{html}</div>", unsafe_allow_html=True)


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


def current_year_projection(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or df["year"].dropna().empty:
        return pd.DataFrame()

    today = date.today()
    current_year = today.year
    current_df = df[df["year"] == current_year].copy()
    if current_df.empty:
        return pd.DataFrame()

    start_of_year = date(current_year, 1, 1)
    end_of_year = date(current_year, 12, 31)
    elapsed_days = (today - start_of_year).days + 1
    total_days = (end_of_year - start_of_year).days + 1

    proj = (
        current_df.groupby("sport_grouped", dropna=False)
        .agg(
            ytd_distance_km=("distance_km", "sum"),
            ytd_time_h=("moving_time_h", "sum"),
            ytd_elevation_m=("elevation_m", "sum"),
            ytd_activities=("id", "count"),
        )
        .reset_index()
    )

    proj["proj_distance_km"] = proj["ytd_distance_km"] / elapsed_days * total_days
    proj["proj_time_h"] = proj["ytd_time_h"] / elapsed_days * total_days
    proj["proj_elevation_m"] = proj["ytd_elevation_m"] / elapsed_days * total_days
    proj["proj_activities"] = proj["ytd_activities"] / elapsed_days * total_days

    prev = (
        df[df["year"] == current_year - 1]
        .groupby("sport_grouped", dropna=False)
        .agg(
            prev_distance_km=("distance_km", "sum"),
            prev_time_h=("moving_time_h", "sum"),
            prev_elevation_m=("elevation_m", "sum"),
            prev_activities=("id", "count"),
        )
        .reset_index()
    )

    proj = proj.merge(prev, on="sport_label", how="left").fillna(0)

    def pct(a: pd.Series, b: pd.Series) -> pd.Series:
        return ((a - b) / b.replace(0, pd.NA) * 100).fillna(0)

    proj["delta_distance_pct"] = pct(proj["proj_distance_km"], proj["prev_distance_km"])
    proj["delta_time_pct"] = pct(proj["proj_time_h"], proj["prev_time_h"])
    proj["delta_elevation_pct"] = pct(proj["proj_elevation_m"], proj["prev_elevation_m"])
    proj["delta_activities_pct"] = pct(proj["proj_activities"], proj["prev_activities"])

    return proj.sort_values("proj_distance_km", ascending=False).reset_index(drop=True)


def top_sports_panels(sport_df: pd.DataFrame) -> dict:
    if sport_df.empty:
        return {"distance": [], "time": [], "elevation": []}

    return {
        "distance": sport_df.sort_values("distance_km", ascending=False)[["sport_label", "distance_km"]].head(3).to_dict("records"),
        "time": sport_df.sort_values("moving_time_h", ascending=False)[["sport_label", "moving_time_h"]].head(3).to_dict("records"),
        "elevation": sport_df.sort_values("elevation_m", ascending=False)[["sport_label", "elevation_m"]].head(3).to_dict("records"),
    }


def metric_col_name(metric_key: str) -> str:
    return {
        "distance_km": "Distanza",
        "moving_time_h": "Tempo",
        "elevation_m": "Dislivello",
    }[metric_key]


# ============================================================
# SETTINGS / CLIENT
# ============================================================

try:
    settings = get_settings()
except Exception:
    st.error("Secrets mancanti o non validi.")
    st.stop()

client = StravaClient(settings)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero-wrap">
        <div class="app-title">Strava Dashboard</div>
        <div class="app-subtitle">Overview completa, analisi avanzate e design mobile-first</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SYNC
# ============================================================

with st.expander("Sincronizzazione dati", expanded=False):
    start_date = st.date_input("Importa attività da", value=date.fromisoformat(settings.default_start_date))
    sync_now = st.button("Sincronizza da Strava", type="primary")

    if sync_now:
        try:
            with st.spinner("Scarico le attività da Strava..."):
                after_ts = iso_to_unix(start_date.isoformat())
                raw = client.list_activities(after_ts=after_ts)
                sync_df = normalize_activities(raw)
                save_activities(sync_df, settings.cache_file)
                st.success(f"Sincronizzazione completata: {len(sync_df)} attività.")
        except Exception as e:
            st.error(f"Errore durante la sincronizzazione: {e}")

base_df = load_activities(settings.cache_file)

if base_df.empty:
    st.markdown(
        "<div class='big-empty'>Nessun dato disponibile. Premi <b>Sincronizza da Strava</b>.</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# ============================================================
# FILTERS
# ============================================================

sports = available_sports(base_df)
years = sorted([int(y) for y in base_df["year"].dropna().unique().tolist()], reverse=True)

st.markdown("<div class='filter-wrap'>", unsafe_allow_html=True)
f1, f2, f3 = st.columns([2.2, 1.2, 1.0])

with f1:
    selected_sports = st.multiselect(
        "Filtro sport",
        options=sports,
        default=[],
        placeholder="Vuoto = tutti gli sport",
        help="Lascia vuoto per visualizzare il totale di tutti gli sport.",
    )

with f2:
    year_options = ["Tutti gli anni"] + [str(y) for y in years]
    selected_year = st.selectbox("Periodo", options=year_options, index=0)

with f3:
    metric_label = st.selectbox("Metrica trend", ["Distanza", "Tempo", "Dislivello"], index=0)

st.markdown("</div>", unsafe_allow_html=True)

selected_years = None if selected_year == "Tutti gli anni" else [int(selected_year)]
selected_metric = {
    "Distanza": "distance_km",
    "Tempo": "moving_time_h",
    "Dislivello": "elevation_m",
}[metric_label]

filtered_df = filter_activities(
    filtered_df = group_small_sports(filtered_df),
    base_df,
    selected_sports=selected_sports if selected_sports else None,
    years=selected_years,
)

if filtered_df.empty:
    st.markdown(
        "<div class='big-empty'>Nessun dato disponibile con i filtri correnti.</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# ============================================================
# PRE-COMPUTE
# ============================================================

kpis = kpi_summary(filtered_df)
distance_compare = compare_vs_previous_year(filtered_df, metric="distance_km")
time_compare = compare_vs_previous_year(filtered_df, metric="moving_time_h")
elev_compare = compare_vs_previous_year(filtered_df, metric="elevation_m")

sport_summary_df = summary_by_sport(filtered_df)
monthly_sport_df = monthly_by_sport(filtered_df)
cumulative_metric_df = cumulative_by_year(filtered_df, metric=selected_metric)
trend_metric_df = trend_monthly(filtered_df, metric=selected_metric)

bp = best_performances(filtered_df)
fav_day = favorite_weekday(filtered_df)
active_week = most_active_week(filtered_df)
main_sport = primary_sport(filtered_df)
buckets = distance_bucket_distribution(filtered_df, "count", "bucket")
records = personal_records(filtered_df)
zones = zone_proxy(filtered_df)
consistency = consistency_score(filtered_df)
proj = current_year_projection(filtered_df)
top_sports = top_sports_panels(sport_summary_df)
month_best_worst = monthly_best_worst(filtered_df, metric="distance_km")


# ============================================================
# TABS
# ============================================================

overview_tab, per_sport_tab, trend_tab, performance_tab, projections_tab, zone_tab = st.tabs(
    ["Overview", "Per sport", "Trend", "Performance", "Proiezioni", "Zone"]
)


# ============================================================
# OVERVIEW
# ============================================================

with overview_tab:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card_html("Attività", fmt_int(kpis["activities"]), f"{fmt_pct(distance_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)
    with c2:
        st.markdown(card_html("Distanza", fmt_km(kpis["distance_km"]), f"{fmt_pct(distance_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)
    with c3:
        st.markdown(card_html("Tempo", fmt_h(kpis["moving_time_h"]), f"{fmt_pct(time_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)
    with c4:
        st.markdown(card_html("Dislivello", fmt_m(kpis["elevation_m"]), f"{fmt_pct(elev_compare['delta_pct'])} vs anno scorso"), unsafe_allow_html=True)

    a, b, c = st.columns([1.9, 1.15, 0.95])

    with a:
        section_open("Andamento mensile", f"{metric_col_name('distance_km')} aggregata per mese e sport")
        if not monthly_sport_df.empty:
            color_map = sport_color_map(monthly_sport_df["sport_label"].dropna().unique())
            fig = px.bar(
                monthly_sport_df,
                x="month",
                y="distance_km",
                color="sport_grouped",
                barmode="stack",
                color_discrete_map=color_map,
            )
            fig = plot_style(fig, height=355)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with b:
        section_open("Distribuzione distanza per sport")
        if not sport_summary_df.empty:
            color_map = sport_color_map(sport_summary_df["sport_label"].dropna().unique())
            fig = px.pie(
                sport_summary_df,
                names="sport_label",
                values="distance_km",
                hole=0.62,
                color="sport_grouped",
                color_discrete_map=color_map,
            )
            fig = plot_style(fig, height=355)
            fig.update_traces(textinfo="percent")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with c:
        section_open("I tuoi numeri chiave")
        st.markdown(mini_stat_html("Attività", fmt_int(kpis["activities"]), "totale periodo selezionato"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Media distanza", fmt_km(kpis["avg_distance_km"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Media tempo", fmt_h(kpis["avg_time_h"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Media dislivello", fmt_m(kpis["avg_elevation_m"]), "per attività"), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Indice di costanza", f"{consistency:.0f}/100", "presenza settimanale"), unsafe_allow_html=True)
        section_close()

    d, e, f = st.columns([1.4, 1.05, 1.0])

    with d:
        section_open("Trend vs anno scorso", "Confronto cumulativo")
        if not cumulative_metric_df.empty:
            color_map = {str(y): "#94c5ff" for y in cumulative_metric_df["year"].astype(str).unique()}
            if str(distance_compare["current_year"]) in color_map:
                color_map[str(distance_compare["current_year"])] = ACCENT

            cumulative_metric_df = cumulative_metric_df.copy()
            cumulative_metric_df["year_str"] = cumulative_metric_df["year"].astype(str)

            fig = px.line(
                cumulative_metric_df,
                x="month_label",
                y="cumulative",
                color="year_str",
                markers=True,
                color_discrete_map=color_map,
            )
            fig = plot_style(fig, height=325)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(
                f"<span class='pill'>Sei a {fmt_pct(distance_compare['delta_pct'])} rispetto al {distance_compare['previous_year']}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div class='big-empty'>Nessun confronto disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with e:
        section_open("Migliori performance")
        if bp.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            for _, row in bp.iterrows():
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{row['value']}</div>
                        <div class="insight-sub">{row['label']} · {row['date']} · f"{SPORT_ICONS.get(row['sport'], '•')} {row['sport']}"</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()

    with f:
        section_open("Zone di frequenza", "Distribuzione attività")
        if zones.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            for _, row in zones.iterrows():
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{row['zone']}</div>
                        <div class="insight-sub">{row['activities_pct']:.0f}% attività · {row['time_pct']:.0f}% tempo</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()

    g, h, i = st.columns(3)
    with g:
        st.markdown(mini_stat_html("Giorno preferito", fav_day["weekday"], f"{fav_day['pct']:.0f}% delle attività"), unsafe_allow_html=True)
    with h:
        st.markdown(mini_stat_html("Settimana più attiva", active_week.get("week", "-"), f"{active_week.get('activities', 0)} attività"), unsafe_allow_html=True)
    with i:
        st.markdown(mini_stat_html("Sport principale", main_sport["sport"], f"{main_sport['pct']:.0f}% della distanza"), unsafe_allow_html=True)


# ============================================================
# PER SPORT
# ============================================================

with per_sport_tab:
    a, b = st.columns([2.0, 0.95])

    with a:
        section_open("Riepilogo per sport")
        show = sport_summary_df.rename(
            columns={
                "sport_label": "Sport",
                "activities": "Attività",
                "distance_km": "Distanza (km)",
                "moving_time_h": "Tempo (h)",
                "elevation_m": "Dislivello (m)",
                "avg_speed_kmh": "Vel. media",
            }
        ).copy()

        numeric_cols = ["Distanza (km)", "Tempo (h)", "Dislivello (m)", "Vel. media"]
        for col in numeric_cols:
            if col in show.columns:
                show[col] = show[col].map(lambda x: f"{x:,.1f}")

        render_html_table(show)
        section_close()

        section_open("Confronto distanza per sport")
        if not sport_summary_df.empty:
            color_map = sport_color_map(sport_summary_df["sport_label"].dropna().unique())
            fig = px.bar(
                sport_summary_df.sort_values("distance_km", ascending=True),
                x="distance_km",
                y="sport_label",
                orientation="h",
                color="sport_grouped",
                color_discrete_map=color_map,
            )
            fig = plot_style(fig, height=355, show_legend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with b:
        section_open("Top sport")
        st.markdown("<div class='tiny' style='margin-bottom:8px;'>per distanza</div>", unsafe_allow_html=True)
        for r in top_sports["distance"]:
            st.markdown(f"<div class='insight-row'><div class='insight-main'>{r['sport_label']}</div><div class='insight-sub'>{fmt_km(r['distance_km'])}</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='tiny' style='margin-top:10px; margin-bottom:8px;'>per tempo</div>", unsafe_allow_html=True)
        for r in top_sports["time"]:
            st.markdown(f"<div class='insight-row'><div class='insight-main'>{r['sport_label']}</div><div class='insight-sub'>{fmt_h(r['moving_time_h'])}</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='tiny' style='margin-top:10px; margin-bottom:8px;'>per dislivello</div>", unsafe_allow_html=True)
        for r in top_sports["elevation"]:
            st.markdown(f"<div class='insight-row'><div class='insight-main'>{r['sport_label']}</div><div class='insight-sub'>{fmt_m(r['elevation_m'])}</div></div>", unsafe_allow_html=True)
        section_close()

        target_distance = max(1.0, kpis["distance_km"] * 1.5)
        progress_pct = min(100.0, (kpis["distance_km"] / target_distance) * 100.0)
        st.markdown(mini_stat_html("Obiettivo annuale", f"{progress_pct:.0f}%", f"{fmt_km(kpis['distance_km'])} / {fmt_km(target_distance)}"), unsafe_allow_html=True)


# ============================================================
# TREND
# ============================================================

with trend_tab:
    a, b = st.columns([1.95, 1.0])

    with a:
        section_open("Trend cumulativo")
        if not cumulative_metric_df.empty:
            temp = cumulative_metric_df.copy()
            temp["year_str"] = temp["year"].astype(str)
            temp = temp.sort_values(["year", "month_num"])

            month_order = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            temp["month_label"] = pd.Categorical(temp["month_label"], categories=month_order, ordered=True)

            color_map = {str(y): "#94c5ff" for y in temp["year"].unique()}
            color_map[str(distance_compare["current_year"])] = ACCENT

            fig = px.line(
                temp,
                x="month_label",
                y="cumulative",
                color="year_str",
                markers=True,
                color_discrete_map=color_map,
                category_orders={"month_label": month_order},
            )
            fig = plot_style(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

        section_open("Trend mensile", f"Metrica: {metric_label}")
        if not trend_metric_df.empty:
            temp_trend = trend_metric_df.copy()
            temp_trend = temp_trend.sort_values(["year", "month_num"])

            month_order = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            temp_trend["month"] = pd.Categorical(temp_trend["month"], categories=month_order, ordered=True)

            if temp_trend["year"].nunique() > 1:
                temp_trend["year_str"] = temp_trend["year"].astype(str)
                color_map = {str(y): "#94c5ff" for y in temp_trend["year"].unique()}
                color_map[str(distance_compare["current_year"])] = ACCENT

                fig = px.line(
                    temp_trend,
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
                    temp_trend,
                    x="month",
                    y=selected_metric,
                    markers=True,
                    line_shape="linear",
                    category_orders={"month": month_order},
                )
                fig.update_traces(line=dict(color=ACCENT, width=3))

            fig = plot_style(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with b:
        section_open("Progresso")
        target_value = max(
            1.0,
            distance_compare["previous"] * 1.10 if distance_compare["previous"] > 0 else kpis["distance_km"] * 1.25,
        )
        progress = min(100.0, (kpis["distance_km"] / target_value) * 100.0)

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
        fig = plot_style(fig, height=265, show_legend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<div class='tiny'>{fmt_km(kpis['distance_km'])} distanza percorsa</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='tiny'>su target {fmt_km(target_value)}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(mini_stat_html("Miglior mese", month_best_worst["best_month"], fmt_km(month_best_worst["best_value"])), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Peggior mese", month_best_worst["worst_month"], fmt_km(month_best_worst["worst_value"])), unsafe_allow_html=True)
        st.markdown(mini_stat_html("Stabilità", f"{consistency:.0f}/100", "indice di costanza"), unsafe_allow_html=True)
        section_close()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Distanza totale", fmt_km(kpis["distance_km"]), fmt_pct(distance_compare["delta_pct"]))
    with m2:
        st.metric("Tempo totale", fmt_h(kpis["moving_time_h"]), fmt_pct(time_compare["delta_pct"]))
    with m3:
        st.metric("Dislivello totale", fmt_m(kpis["elevation_m"]), fmt_pct(elev_compare["delta_pct"]))
    with m4:
        st.metric("Attività totali", fmt_int(kpis["activities"]))


# ============================================================
# PERFORMANCE
# ============================================================

with performance_tab:
    a, b, c = st.columns([1.0, 1.1, 0.95])

    with a:
        section_open("Top 5 - più lunghe distanze")
        top5 = filtered_df.sort_values("distance_km", ascending=False).head(5).copy()
        if top5.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            top5["date_str"] = pd.to_datetime(top5["start_date_local"]).dt.strftime("%d %b %Y")
            for idx, (_, row) in enumerate(top5.iterrows(), start=1):
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{idx}. {row['distance_km']:.1f} km</div>
                        <div class="insight-sub">{row['sport_label']} · {row['date_str']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()

    with b:
        section_open("Distribuzione attività per distanza")
        if not buckets.empty:
            fig = px.bar(buckets, x="bucket", y="count")
            fig.update_traces(marker_color=ACCENT)
            fig = plot_style(fig, height=340, show_legend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with c:
        section_open("Record personali")
        if records.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            for _, row in records.iterrows():
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-main">{row['record']}</div>
                        <div class="insight-sub">{row['value']} · {row['date']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        section_close()


# ============================================================
# PROJECTIONS
# ============================================================

with projections_tab:
    a, b = st.columns([1.45, 1.0])

    with a:
        section_open("Proiezione fine anno per sport")
        if proj.empty:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        else:
            proj_show = proj[[
                "sport_label",
                "proj_distance_km",
                "proj_time_h",
                "proj_elevation_m",
                "proj_activities",
                "delta_distance_pct",
                "delta_time_pct",
                "delta_elevation_pct",
                "delta_activities_pct",
            ]].rename(
                columns={
                    "sport_label": "Sport",
                    "proj_distance_km": "Distanza (km)",
                    "proj_time_h": "Tempo (h)",
                    "proj_elevation_m": "Dislivello (m)",
                    "proj_activities": "Attività",
                    "delta_distance_pct": "Δ Distanza %",
                    "delta_time_pct": "Δ Tempo %",
                    "delta_elevation_pct": "Δ Dislivello %",
                    "delta_activities_pct": "Δ Attività %",
                }
            ).copy()

            for col in ["Distanza (km)", "Tempo (h)", "Dislivello (m)", "Attività", "Δ Distanza %", "Δ Tempo %", "Δ Dislivello %", "Δ Attività %"]:
                if col in proj_show.columns:
                    proj_show[col] = proj_show[col].map(lambda x: f"{x:,.1f}")

            render_html_table(proj_show)
        section_close()

        section_open("Proiezione distanza totale")
        if not proj.empty:
            color_map = sport_color_map(proj["sport_label"].dropna().unique())
            fig = px.bar(
                proj,
                x="sport_label",
                y="proj_distance_km",
                color="sport_grouped",
                color_discrete_map=color_map,
            )
            fig = plot_style(fig, height=320, show_legend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with b:
        section_open("Numeri chiave")
        if not proj.empty:
            total_proj_km = float(proj["proj_distance_km"].sum())
            total_proj_h = float(proj["proj_time_h"].sum())
            total_proj_m = float(proj["proj_elevation_m"].sum())
            total_proj_a = float(proj["proj_activities"].sum())

            st.markdown(mini_stat_html("Proiezione distanza", fmt_km(total_proj_km), "anno in corso"), unsafe_allow_html=True)
            st.markdown(mini_stat_html("Proiezione tempo", fmt_h(total_proj_h), "anno in corso"), unsafe_allow_html=True)
            st.markdown(mini_stat_html("Proiezione dislivello", fmt_m(total_proj_m), "anno in corso"), unsafe_allow_html=True)
            st.markdown(mini_stat_html("Proiezione attività", fmt_int(total_proj_a), "anno in corso"), unsafe_allow_html=True)

            prev_total = distance_compare["previous"]
            reach_pct = 100.0 if prev_total <= 0 else min(100.0, (total_proj_km / prev_total) * 100.0)
            st.markdown(
                f"""
                <div class="mini-stat">
                    <div class="mini-label">Probabilità di superare l'anno scorso</div>
                    <div class="mini-value">{reach_pct:.0f}%</div>
                    <div class="mini-sub">con il ritmo attuale</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()


# ============================================================
# ZONES
# ============================================================

with zone_tab:
    a, b = st.columns([1.0, 1.0])

    with a:
        section_open("Distribuzione attività per zona")
        if not zones.empty:
            zone_colors = {
                "Zona 1 (Recupero)": "#60a5fa",
                "Zona 2 (Endurance)": "#4ade80",
                "Zona 3 (Tempo)": "#f59e0b",
                "Zona 4 (Soglia)": "#f97316",
                "Zona 5 (VO2 Max)": "#ef4444",
            }
            fig = px.pie(
                zones,
                names="zone",
                values="activities",
                hole=0.58,
                color="zone",
                color_discrete_map=zone_colors,
            )
            fig = plot_style(fig, height=320)
            fig.update_traces(textinfo="percent")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    with b:
        section_open("Tempo in zona (ore)")
        if not zones.empty:
            zone_colors = {
                "Zona 1 (Recupero)": "#60a5fa",
                "Zona 2 (Endurance)": "#4ade80",
                "Zona 3 (Tempo)": "#f59e0b",
                "Zona 4 (Soglia)": "#f97316",
                "Zona 5 (VO2 Max)": "#ef4444",
            }
            fig = px.bar(
                zones.sort_values("moving_time_h", ascending=True),
                x="moving_time_h",
                y="zone",
                orientation="h",
                color="zone",
                color_discrete_map=zone_colors,
            )
            fig = plot_style(fig, height=320, show_legend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='big-empty'>Nessun dato disponibile.</div>", unsafe_allow_html=True)
        section_close()

    if not zones.empty:
        zone2_pct = float(zones.loc[zones["zone"] == "Zona 2 (Endurance)", "time_pct"].sum()) if "Zona 2 (Endurance)" in zones["zone"].astype(str).tolist() else 0.0
        avg_intensity = float(filtered_df["effort_score"].mean()) if "effort_score" in filtered_df.columns else 0.0
        weekly_load = float(filtered_df.groupby(["year", "week"])["moving_time_h"].sum().mean()) if not filtered_df.empty else 0.0
        trend_int = float(filtered_df["effort_score"].tail(min(10, len(filtered_df))).mean()) if not filtered_df.empty else 0.0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(mini_stat_html("Intensità media", f"{avg_intensity:.1f}", "su 5 zone proxy"), unsafe_allow_html=True)
        with c2:
            st.markdown(mini_stat_html("Attività in zona 2", f"{zone2_pct:.0f}%", "tempo in zona 2"), unsafe_allow_html=True)
        with c3:
            st.markdown(mini_stat_html("Carico settimanale", f"{weekly_load:.1f} h", "media ultime settimane"), unsafe_allow_html=True)
        with c4:
            st.markdown(mini_stat_html("Trend intensità", f"{trend_int:.0f}", "proxy score recente"), unsafe_allow_html=True)

        section_open("Distribuzione tempo in zona (%)")
        zone_colors = {
            "Zona 1 (Recupero)": "#60a5fa",
            "Zona 2 (Endurance)": "#4ade80",
            "Zona 3 (Tempo)": "#f59e0b",
            "Zona 4 (Soglia)": "#f97316",
            "Zona 5 (VO2 Max)": "#ef4444",
        }
        fig = px.bar(
            zones,
            x="zone",
            y="time_pct",
            color="zone",
            color_discrete_map=zone_colors,
        )
        fig = plot_style(fig, height=270, show_legend=False)
        st.plotly_chart(fig, use_container_width=True)
        section_close()
