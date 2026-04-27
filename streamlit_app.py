from __future__ import annotations

from datetime import date

import streamlit as st

from app.config import get_settings, iso_to_unix
from app.metrics import (
    available_sports,
    best_performances,
    compare_vs_previous_year,
    consistency_score,
    cumulative_by_year,
    current_year_projection,
    distance_bucket_distribution,
    favorite_weekday,
    filter_activities,
    group_small_sports,
    kpi_summary,
    monthly_best_worst,
    monthly_by_sport,
    most_active_week,
    normalize_activities,
    personal_records,
    primary_sport,
    summary_by_sport,
    top_sports_panels,
    trend_monthly,
    zone_proxy,
)
from app.storage import load_activities, save_activities
from app.strava_api import StravaClient
from app.theme import inject_global_css, render_header
from app.views_overview import render_overview
from app.views_per_sport import render_per_sport
from app.views_trend import render_trend
from app.views_performance import render_performance
from app.views_projections import render_projections
from app.views_zones import render_zones


st.set_page_config(page_title="Strava Dashboard", page_icon="🚴", layout="wide")
inject_global_css()

try:
    settings = get_settings()
except Exception:
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
render_header()

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
    st.markdown("<div class='big-empty'>Nessun dato disponibile. Premi <b>Sincronizza da Strava</b>.</div>", unsafe_allow_html=True)
    st.stop()

sports = available_sports(base_df)
years = sorted([int(y) for y in base_df["year"].dropna().unique().tolist()], reverse=True)

st.markdown("<div class='filter-wrap'>", unsafe_allow_html=True)
f1, f2, f3 = st.columns([2.2, 1.2, 1.0])
with f1:
    selected_sports = st.multiselect("Filtro sport", options=sports, default=[], placeholder="Vuoto = tutti gli sport", help="Lascia vuoto per visualizzare il totale di tutti gli sport.")
with f2:
    year_options = ["Tutti gli anni"] + [str(y) for y in years]
    selected_year = st.selectbox("Periodo", options=year_options, index=0)
with f3:
    metric_label = st.selectbox("Metrica trend", ["Distanza", "Tempo", "Dislivello"], index=0)
st.markdown("</div>", unsafe_allow_html=True)

selected_years = None if selected_year == "Tutti gli anni" else [int(selected_year)]
selected_metric = {"Distanza": "distance_km", "Tempo": "moving_time_h", "Dislivello": "elevation_m"}[metric_label]

filtered_df = filter_activities(base_df, selected_sports=selected_sports if selected_sports else None, years=selected_years)
filtered_df = group_small_sports(filtered_df)

if filtered_df.empty:
    st.markdown("<div class='big-empty'>Nessun dato disponibile con i filtri correnti.</div>", unsafe_allow_html=True)
    st.stop()

prepared = {
    "kpis": kpi_summary(filtered_df),
    "distance_compare": compare_vs_previous_year(filtered_df, metric="distance_km"),
    "time_compare": compare_vs_previous_year(filtered_df, metric="moving_time_h"),
    "elev_compare": compare_vs_previous_year(filtered_df, metric="elevation_m"),
    "sport_summary_df": summary_by_sport(filtered_df),
    "monthly_sport_df": monthly_by_sport(filtered_df),
    "cumulative_metric_df": cumulative_by_year(filtered_df, metric=selected_metric),
    "trend_metric_df": trend_monthly(filtered_df, metric=selected_metric),
    "best_performances": best_performances(filtered_df),
    "favorite_weekday": favorite_weekday(filtered_df),
    "most_active_week": most_active_week(filtered_df),
    "primary_sport": primary_sport(filtered_df),
    "buckets": distance_bucket_distribution(filtered_df, "count", "bucket"),
    "records": personal_records(filtered_df),
    "zones": zone_proxy(filtered_df),
    "consistency": consistency_score(filtered_df),
    "proj": current_year_projection(filtered_df),
    "month_best_worst": monthly_best_worst(filtered_df, metric="distance_km"),
}
prepared["top_sports"] = top_sports_panels(prepared["sport_summary_df"])

overview_tab, per_sport_tab, trend_tab, performance_tab, projections_tab, zone_tab = st.tabs([
    "Overview", "Per sport", "Trend", "Performance", "Proiezioni", "Zone"
])

with overview_tab:
    render_overview(prepared)
with per_sport_tab:
    render_per_sport(prepared)
with trend_tab:
    render_trend(prepared, metric_label=metric_label, selected_metric=selected_metric)
with performance_tab:
    render_performance(prepared, filtered_df)
with projections_tab:
    render_projections(prepared)
with zone_tab:
    render_zones(prepared, filtered_df)
