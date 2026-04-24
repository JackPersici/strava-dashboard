from __future__ import annotations

from datetime import date
import math

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


st.set_page_config(
    page_title="Strava Dashboard",
    page_icon="🚴",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .kpi-card {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 18px;
        padding: 18px 18px 14px 18px;
        color: white;
        min-height: 132px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.18);
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #cbd5e1;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 8px;
    }
    .kpi-delta {
        font-size: 0.92rem;
        color: #86efac;
    }
    .panel {
        background: #0f172a;
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 18px;
        padding: 16px 16px 8px 16px;
        color: white;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.14);
        margin-bottom: 14px;
    }
    .panel h4 {
        margin-top: 0;
        margin-bottom: 10px;
        color: white;
    }
    .tiny {
        color: #94a3b8;
        font-size: 0.88rem;
    }
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        background: rgba(249, 115, 22, 0.12);
        color: #fb923c;
        border: 1px solid rgba(249, 115, 22, 0.25);
    }
    .hint {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: -4px;
        margin-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def fmt_km(v: float) -> str:
    return f"{v:,.1f} km"


def fmt_h(v: float) -> str:
    return f"{v:,.1f} h"


def fmt_m(v: float) -> str:
    return f"{v:,.0f} m"


def fmt_pct(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.0f}%"


def build_kpi_card(label: str, value: str, delta_text: str = "") -> str:
    delta_html = f"<div class='kpi-delta'>{delta_text}</div>" if delta_text else "<div class='kpi-delta'>&nbsp;</div>"
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


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
        current_df.groupby("sport_label", dropna=False)
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

    previous = (
        df[df["year"] == current_year - 1]
        .groupby("sport_label", dropna=False)
        .agg(
            prev_distance_km=("distance_km", "sum"),
            prev_time_h=("moving_time_h", "sum"),
            prev_elevation_m=("elevation_m", "sum"),
            prev_activities=("id", "count"),
        )
        .reset_index()
    )

    proj = proj.merge(previous, on="sport_label", how="left").fillna(0)

    def pct(a: pd.Series, b: pd.Series) -> pd.Series:
        return ((a - b) / b.replace(0, pd.NA) * 100).fillna(0)

    proj["delta_distance_pct"] = pct(proj["proj_distance_km"], proj["prev_distance_km"])
    proj["delta_time_pct"] = pct(proj["proj_time_h"], proj["prev_time_h"])
    proj["delta_elevation_pct"] = pct(proj["proj_elevation_m"], proj["prev_elevation_m"])
    proj["delta_activities_pct"] = pct(proj["proj_activities"], proj["prev_activities"])

    proj = proj.sort_values("proj_distance_km", ascending=False).reset_index(drop=True)
    return proj


def top_sports_panels(sport_df: pd.DataFrame) -> dict:
    if sport_df.empty:
        return {"distance": [], "time": [], "elevation": []}

    by_distance = sport_df.sort_values("distance_km", ascending=False).head(3)
    by_time = sport_df.sort_values("moving_time_h", ascending=False).head(3)
    by_elev = sport_df.sort_values("elevation_m", ascending=False).head(3)

    return {
        "distance": by_distance[["sport_label", "distance_km"]].to_dict("records"),
        "time": by_time[["sport_label", "moving_time_h"]].to_dict("records"),
        "elevation": by_elev[["sport_label", "elevation_m"]].to_dict("records"),
    }


def best_worst_month_cards(df: pd.DataFrame, metric_col: str) -> dict:
    res = monthly_best_worst(df, metric=metric_col)
    return res


def make_plot_layout(fig: go.Figure, title: str | None = None, height: int = 320) -> go.Figure:
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=False, color="#cbd5e1")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", color="#cbd5e1")
    return fig


# ------------------------------------------------------------
# Load settings / client
# ------------------------------------------------------------

try:
    settings = get_settings()
except Exception:
    st.title("Strava Dashboard")
    st.error("Secrets mancanti o non validi.")
    st.info("Su Streamlit Cloud inserisci i secrets da: Manage app -> Settings -> Secrets.")
    st.code(
        '''STRAVA_CLIENT_ID = "114269"
STRAVA_CLIENT_SECRET = "IL_TUO_CLIENT_SECRET"
STRAVA_REFRESH_TOKEN = "IL_TUO_REFRESH_TOKEN"
STRAVA_SCOPE = "read,activity:read_all"''',
        language="toml",
    )
    st.stop()

client = StravaClient(settings)

# ------------------------------------------------------------
# Header + Sync
# ------------------------------------------------------------

st.title("Strava Dashboard")
st.caption("Overview, Trend, Performance, Proiezioni e Zone — responsive per iPhone e PC")

with st.expander("Sincronizzazione dati", expanded=True):
    start_date = st.date_input("Importa attività da", value=date.fromisoformat(settings.default_start_date))
    sync_now = st.button("Sincronizza da Strava", type="primary")

    if sync_now:
        try:
            with st.spinner("Scarico le attività da Strava..."):
                after_ts = iso_to_unix(start_date.isoformat())
                raw = client.list_activities(after_ts=after_ts)
                df_sync = normalize_activities(raw)
                save_activities(df_sync, settings.cache_file)
                st.success(f"Sincronizzazione completata: {len(df_sync)} attività.")
        except Exception as e:
            st.error(f"Errore durante la sincronizzazione: {e}")

base_df = load_activities(settings.cache_file)

if base_df.empty:
    st.info("Nessun dato disponibile per ora. Premi 'Sincronizza da Strava'.")
    st.stop()

# ------------------------------------------------------------
# Filters
# ------------------------------------------------------------

sports = available_sports(base_df)
all_years = sorted([int(y) for y in base_df["year"].dropna().unique().tolist()], reverse=True)

c1, c2, c3 = st.columns([2.4, 1.3, 1.0])

with c1:
    selected_sports = st.multiselect(
        "Filtro sport",
        options=sports,
        default=[],
        placeholder="Vuoto = tutti gli sport",
        help="Se non selezioni nulla, la dashboard mostra tutti gli sport.",
    )

with c2:
    year_options = ["Tutti gli anni"] + [str(y) for y in all_years]
    selected_year = st.selectbox("Periodo", options=year_options, index=0)

with c3:
    metric_label = st.selectbox("Metrica trend", ["Distanza", "Tempo", "Dislivello"], index=0)

selected_years = None if selected_year == "Tutti gli anni" else [int(selected_year)]
selected_metric = {
    "Distanza": "distance_km",
    "Tempo": "moving_time_h",
    "Dislivello": "elevation_m",
}[metric_label]

filtered_df = filter_activities(
    base_df,
    selected_sports=selected_sports if selected_sports else None,
    years=selected_years,
)

if filtered_df.empty:
    st.warning("Nessun dato disponibile con i filtri correnti.")
    st.stop()

# ------------------------------------------------------------
# Precompute
# ------------------------------------------------------------

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
bw_distance = best_worst_month_cards(filtered_df, "distance_km")

# ------------------------------------------------------------
# Tabs
# ------------------------------------------------------------

overview_tab, per_sport_tab, trend_tab, performance_tab, projections_tab, zone_tab = st.tabs(
    ["Overview", "Per sport", "Trend", "Performance", "Proiezioni", "Zone"]
)

# ------------------------------------------------------------
# Overview
# ------------------------------------------------------------

with overview_tab:
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            build_kpi_card("Attività", f"{kpis['activities']}", fmt_pct(distance_compare["delta_pct"]) + " vs anno scorso"),
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            build_kpi_card("Distanza", fmt_km(kpis["distance_km"]), fmt_pct(distance_compare["delta_pct"]) + " vs anno scorso"),
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            build_kpi_card("Tempo", fmt_h(kpis["moving_time_h"]), fmt_pct(time_compare["delta_pct"]) + " vs anno scorso"),
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            build_kpi_card("Dislivello", fmt_m(kpis["elevation_m"]), fmt_pct(elev_compare["delta_pct"]) + " vs anno scorso"),
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns([1.9, 1.2, 1.0])

    with c1:
        st.markdown("<div class='panel'><h4>Andamento mensile</h4></div>", unsafe_allow_html=True)
        if not monthly_sport_df.empty:
            fig = px.bar(
                monthly_sport_df,
                x="month",
                y="distance_km",
                color="sport_label",
                barmode="stack",
            )
            fig = make_plot_layout(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("<div class='panel'><h4>Distribuzione distanza per sport</h4></div>", unsafe_allow_html=True)
        if not sport_summary_df.empty:
            fig = px.pie(
                sport_summary_df,
                names="sport_label",
                values="distance_km",
                hole=0.55,
            )
            fig = make_plot_layout(fig, height=340)
            st.plotly_chart(fig, use_container_width=True)

    with c3:
        st.markdown("<div class='panel'><h4>I tuoi numeri chiave</h4></div>", unsafe_allow_html=True)
        st.markdown(f"**{kpis['activities']}** attività")
        st.markdown(f"**{fmt_km(kpis['avg_distance_km'])}** media distanza per attività")
        st.markdown(f"**{fmt_h(kpis['avg_time_h'])}** media tempo per attività")
        st.markdown(f"**{fmt_m(kpis['avg_elevation_m'])}** media dislivello per attività")
        st.markdown(f"**{consistency:.0f}/100** indice di costanza")

    c4, c5, c6 = st.columns([1.4, 1.0, 1.0])

    with c4:
        st.markdown("<div class='panel'><h4>Trend vs anno scorso</h4></div>", unsafe_allow_html=True)
        if not cumulative_metric_df.empty:
            fig = px.line(
                cumulative_metric_df,
                x="month_label",
                y="cumulative",
                color="year",
                markers=True,
            )
            fig = make_plot_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(
                f"<div class='pill'>Sei a {fmt_pct(distance_compare['delta_pct'])} rispetto al {distance_compare['previous_year']}</div>",
                unsafe_allow_html=True,
            )

    with c5:
        st.markdown("<div class='panel'><h4>Migliori performance</h4></div>", unsafe_allow_html=True)
        if bp.empty:
            st.info("Nessun dato disponibile.")
        else:
            for _, row in bp.iterrows():
                st.markdown(
                    f"""**{row['value']}**
<span class='tiny'>{row['label']} · {row['date']} · {row['sport']}</span>""",
                    unsafe_allow_html=True,
                )
                st.divider()

    with c6:
        st.markdown("<div class='panel'><h4>Zone di frequenza</h4></div>", unsafe_allow_html=True)
        if zones.empty:
            st.info("Nessun dato disponibile.")
        else:
            for _, row in zones.iterrows():
                st.markdown(f"**{row['zone']}** — {row['activities_pct']:.0f}% attività")

    c7, c8, c9 = st.columns(3)
    with c7:
        st.markdown(
            f"""
            <div class="panel">
                <h4>Giorno preferito</h4>
                <div class="kpi-value" style="font-size:1.4rem;">{fav_day['weekday']}</div>
                <div class="tiny">{fav_day['pct']:.0f}% delle attività</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            f"""
            <div class="panel">
                <h4>Settimana più attiva</h4>
                <div class="kpi-value" style="font-size:1.4rem;">{active_week.get('week', '-')}</div>
                <div class="tiny">{active_week.get('activities', 0)} attività</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c9:
        st.markdown(
            f"""
            <div class="panel">
                <h4>Sport principale</h4>
                <div class="kpi-value" style="font-size:1.4rem;">{main_sport['sport']}</div>
                <div class="tiny">{main_sport['pct']:.0f}% della distanza</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# Per sport
# ------------------------------------------------------------

with per_sport_tab:
    c1, c2 = st.columns([2.0, 1.0])

    with c1:
        st.markdown("<div class='panel'><h4>Riepilogo per sport</h4></div>", unsafe_allow_html=True)
        show = sport_summary_df.rename(
            columns={
                "sport_label": "Sport",
                "activities": "Attività",
                "distance_km": "Distanza",
                "moving_time_h": "Tempo",
                "elevation_m": "Dislivello",
                "avg_speed_kmh": "Vel. media",
            }
        )
        st.dataframe(show, use_container_width=True, hide_index=True)

        st.markdown("<div class='panel'><h4>Confronto distanza per sport</h4></div>", unsafe_allow_html=True)
        fig = px.bar(
            sport_summary_df.sort_values("distance_km", ascending=True),
            x="distance_km",
            y="sport_label",
            orientation="h",
        )
        fig = make_plot_layout(fig, height=330)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("<div class='panel'><h4>Top sport</h4></div>", unsafe_allow_html=True)

        st.markdown("**Per distanza**")
        for r in top_sports["distance"]:
            st.markdown(f"{r['sport_label']} — {fmt_km(r['distance_km'])}")

        st.divider()

        st.markdown("**Per tempo**")
        for r in top_sports["time"]:
            st.markdown(f"{r['sport_label']} — {fmt_h(r['moving_time_h'])}")

        st.divider()

        st.markdown("**Per dislivello**")
        for r in top_sports["elevation"]:
            st.markdown(f"{r['sport_label']} — {fmt_m(r['elevation_m'])}")

        target_distance = max(1.0, kpis["distance_km"] * 1.5)
        progress_pct = min(100.0, (kpis["distance_km"] / target_distance) * 100.0)

        st.markdown(
            f"""
            <div class="panel">
                <h4>Obiettivo annuale</h4>
                <div class="kpi-value" style="font-size:1.4rem;">{progress_pct:.0f}%</div>
                <div class="tiny">{fmt_km(kpis['distance_km'])} / {fmt_km(target_distance)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# Trend
# ------------------------------------------------------------

with trend_tab:
    c1, c2 = st.columns([2.0, 1.0])

    with c1:
        st.markdown("<div class='panel'><h4>Trend cumulativo</h4></div>", unsafe_allow_html=True)
        if not cumulative_metric_df.empty:
            fig = px.line(
                cumulative_metric_df,
                x="month_label",
                y="cumulative",
                color="year",
                markers=True,
            )
            fig = make_plot_layout(fig, height=330)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<div class='panel'><h4>Trend mensile</h4></div>", unsafe_allow_html=True)
        if not trend_metric_df.empty:
            fig = px.line(
                trend_metric_df,
                x="month",
                y=selected_metric,
                markers=True,
            )
            fig = make_plot_layout(fig, height=330)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("<div class='panel'><h4>Progresso</h4></div>", unsafe_allow_html=True)
        target_value = max(1.0, distance_compare["previous"] * 1.10 if distance_compare["previous"] > 0 else kpis["distance_km"] * 1.25)
        progress = min(100.0, (kpis["distance_km"] / target_value) * 100.0)

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=progress,
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#22c55e"},
                    "bgcolor": "#1f2937",
                    "borderwidth": 0,
                },
            )
        )
        fig = make_plot_layout(fig, height=250)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"**{fmt_km(kpis['distance_km'])}** distanza percorsa")
        st.markdown(f"<span class='tiny'>su target {fmt_km(target_value)}</span>", unsafe_allow_html=True)

        st.divider()

        st.markdown("**Miglior mese**")
        st.markdown(f"{bw_distance['best_month']} — {fmt_km(bw_distance['best_value'])}")

        st.markdown("**Peggior mese**")
        st.markdown(f"{bw_distance['worst_month']} — {fmt_km(bw_distance['worst_value'])}")

        st.markdown("**Stabilità**")
        st.markdown(f"{consistency:.0f}/100")

    c3, c4, c5, c6 = st.columns(4)
    with c3:
        st.metric("Distanza totale", fmt_km(kpis["distance_km"]), fmt_pct(distance_compare["delta_pct"]))
    with c4:
        st.metric("Tempo totale", fmt_h(kpis["moving_time_h"]), fmt_pct(time_compare["delta_pct"]))
    with c5:
        st.metric("Dislivello totale", fmt_m(kpis["elevation_m"]), fmt_pct(elev_compare["delta_pct"]))
    with c6:
        st.metric("Attività totali", f"{kpis['activities']}", None)

# ------------------------------------------------------------
# Performance
# ------------------------------------------------------------

with performance_tab:
    c1, c2, c3 = st.columns([1.1, 1.2, 1.0])

    with c1:
        st.markdown("<div class='panel'><h4>Top 5 - più lunghe distanze</h4></div>", unsafe_allow_html=True)
        rank_show = filtered_df.sort_values("distance_km", ascending=False).head(5).copy()
        if rank_show.empty:
            st.info("Nessun dato disponibile.")
        else:
            rank_show["date_str"] = pd.to_datetime(rank_show["start_date_local"]).dt.strftime("%d %b %Y")
            for idx, (_, row) in enumerate(rank_show.iterrows(), start=1):
                st.markdown(
                    f"""**{idx}. {row['distance_km']:.1f} km**
<span class='tiny'>{row['sport_label']} · {row['date_str']}</span>""",
                    unsafe_allow_html=True,
                )
                st.divider()

    with c2:
        st.markdown("<div class='panel'><h4>Distribuzione attività per distanza</h4></div>", unsafe_allow_html=True)
        if not buckets.empty:
            fig = px.bar(buckets, x="bucket", y="count")
            fig = make_plot_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)

    with c3:
        st.markdown("<div class='panel'><h4>Record personali</h4></div>", unsafe_allow_html=True)
        if records.empty:
            st.info("Nessun dato disponibile.")
        else:
            for _, row in records.iterrows():
                st.markdown(
                    f"""**{row['record']}**
<span class='tiny'>{row['value']} · {row['date']}</span>""",
                    unsafe_allow_html=True,
                )
                st.divider()

# ------------------------------------------------------------
# Proiezioni
# ------------------------------------------------------------

with projections_tab:
    c1, c2 = st.columns([1.4, 1.0])

    with c1:
        st.markdown("<div class='panel'><h4>Proiezione fine anno per sport</h4></div>", unsafe_allow_html=True)
        if proj.empty:
            st.info("Nessun dato disponibile.")
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
            )
            st.dataframe(proj_show, use_container_width=True, hide_index=True)

        st.markdown("<div class='panel'><h4>Proiezione distanza totale</h4></div>", unsafe_allow_html=True)
        if not proj.empty:
            fig = px.bar(proj, x="sport_label", y="proj_distance_km")
            fig = make_plot_layout(fig, height=330)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("<div class='panel'><h4>Numeri chiave</h4></div>", unsafe_allow_html=True)
        if not proj.empty:
            total_proj_km = float(proj["proj_distance_km"].sum())
            total_proj_h = float(proj["proj_time_h"].sum())
            total_proj_m = float(proj["proj_elevation_m"].sum())
            total_proj_acts = float(proj["proj_activities"].sum())

            st.metric("Proiezione 2025/anno in corso - km", fmt_km(total_proj_km))
            st.metric("Proiezione tempo", fmt_h(total_proj_h))
            st.metric("Proiezione dislivello", fmt_m(total_proj_m))
            st.metric("Proiezione attività", f"{total_proj_acts:.0f}")

            prev_total = distance_compare["previous"]
            reach_pct = 100.0 if prev_total <= 0 else (total_proj_km / prev_total) * 100.0
            reach_pct = max(0.0, reach_pct)

            st.divider()
            st.markdown(f"**Probabilità di superare l'anno scorso:** {min(reach_pct, 100):.0f}%")
        else:
            st.info("Nessun dato disponibile.")

# ------------------------------------------------------------
# Zone
# ------------------------------------------------------------

with zone_tab:
    c1, c2 = st.columns([1.0, 1.0])

    with c1:
        st.markdown("<div class='panel'><h4>Distribuzione attività per zona</h4></div>", unsafe_allow_html=True)
        if zones.empty:
            st.info("Nessun dato disponibile.")
        else:
            fig = px.pie(zones, names="zone", values="activities", hole=0.5)
            fig = make_plot_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("<div class='panel'><h4>Tempo in zona (ore)</h4></div>", unsafe_allow_html=True)
        if not zones.empty:
            fig = px.bar(
                zones.sort_values("moving_time_h", ascending=True),
                x="moving_time_h",
                y="zone",
                orientation="h",
            )
            fig = make_plot_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)

    c3, c4, c5, c6 = st.columns(4)
    if not zones.empty:
        zone2_pct = float(zones.loc[zones["zone"] == "Zona 2 (Endurance)", "time_pct"].sum()) if "Zona 2 (Endurance)" in zones["zone"].astype(str).tolist() else 0.0
        avg_intensity = float(filtered_df["effort_score"].mean()) if "effort_score" in filtered_df.columns else 0.0
        weekly_load = float(filtered_df.groupby(["year", "week"])["moving_time_h"].sum().mean()) if not filtered_df.empty else 0.0
        intensity_delta = float(filtered_df["effort_score"].tail(min(10, len(filtered_df))).mean()) if not filtered_df.empty else 0.0

        with c3:
            st.metric("Intensità media", f"{avg_intensity:.1f}")
        with c4:
            st.metric("Attività in zona 2", f"{zone2_pct:.0f}%")
        with c5:
            st.metric("Carico settimanale", f"{weekly_load:.1f} h")
        with c6:
            st.metric("Trend intensità", f"{intensity_delta:.0f}")

        st.markdown("<div class='panel'><h4>Distribuzione tempo in zona (%)</h4></div>", unsafe_allow_html=True)
        fig = px.bar(zones, x="zone", y="time_pct")
        fig = make_plot_layout(fig, height=260)
        st.plotly_chart(fig, use_container_width=True)
