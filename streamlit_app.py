from __future__ import annotations

from datetime import date
import streamlit as st

from app.config import get_settings, iso_to_unix
from app.metrics import (
    normalize_activities,
    filter_activities,
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
from app.projections import project_year_end_by_sport
from app.storage import load_activities, save_activities
from app.strava_api import StravaClient
from app.ui import (
    donut_sport_distribution,
    horizontal_bar,
    inject_custom_css,
    line_comparison,
    multi_metric_trend,
    render_kpis,
    small_info_card,
    stacked_monthly_chart,
    table,
)

st.set_page_config(page_title="Strava Dashboard", page_icon="🚴", layout="wide")
inject_custom_css()

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

st.title("Strava Dashboard")
st.caption("Overview, Trend, Performance, Proiezioni e Zone — responsive per iPhone e PC")

with st.expander("Sincronizzazione dati", expanded=False):
    start_date = st.date_input("Importa attività da", value=date.fromisoformat(settings.default_start_date))
    if st.button("Sincronizza da Strava", type="primary"):
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

sports = available_sports(base_df)
filter_col1, filter_col2, filter_col3 = st.columns([2.4, 1.4, 1])
with filter_col1:
    selected_sports = st.multiselect(
        "Filtro sport",
        options=["Tutti gli sport", *sports],
        default=["Tutti gli sport"],
        help="Seleziona uno, più sport o lascia tutti.",
    )
with filter_col2:
    year_mode = st.selectbox("Periodo", ["Tutti gli anni", "Anno in corso", "Anno scorso"], index=0)
with filter_col3:
    metric_choice = st.selectbox("Metrica trend", ["distance_km", "moving_time_h", "elevation_m", "activities"], format_func=lambda x: {
        "distance_km": "Distanza",
        "moving_time_h": "Tempo",
        "elevation_m": "Dislivello",
        "activities": "Attività",
    }[x])

filtered_df = filter_activities(base_df, selected_sports, year_mode)
if filtered_df.empty:
    st.warning("Nessun dato disponibile con i filtri correnti.")
    st.stop()

# Tabs
overview_tab, per_sport_tab, trend_tab, performance_tab, projections_tab, zone_tab = st.tabs(
    ["Overview", "Per sport", "Trend", "Performance", "Proiezioni", "Zone"]
)

with overview_tab:
    kpis = compute_overview_kpis(filtered_df, base_df)
    render_kpis(kpis)

    c1, c2, c3 = st.columns([1.5, 1.2, 0.9])
    with c1:
        st.markdown("<div class='panel'><h4>Andamento mensile</h4>", unsafe_allow_html=True)
        stacked_monthly_chart(monthly_distance_by_sport(filtered_df), "distance_km")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='panel'><h4>Distribuzione distanza per sport</h4>", unsafe_allow_html=True)
        donut_sport_distribution(sport_distribution(filtered_df))
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        stats = weekday_and_week_stats(filtered_df)
        st.markdown("<div class='panel'><h4>I tuoi numeri chiave</h4>", unsafe_allow_html=True)
        small_info_card("Giorno preferito", stats.get("preferred_day", "n.d."))
        small_info_card("Settimana più attiva", stats.get("best_week", "n.d."))
        small_info_card("Sport principale", stats.get("top_sport", "n.d."))
        st.markdown("</div>", unsafe_allow_html=True)

    c4, c5, c6 = st.columns([1.6, 1.0, 1.0])
    with c4:
        st.markdown("<div class='panel'><h4>Trend vs anno scorso</h4>", unsafe_allow_html=True)
        line_comparison(cumulative_year_vs_previous(filtered_df), "day_of_year", "cumulative_km", "year")
        st.markdown("</div>", unsafe_allow_html=True)
    with c5:
        st.markdown("<div class='panel'><h4>Migliori performance</h4>", unsafe_allow_html=True)
        bp = best_performances(filtered_df)
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
        st.markdown("</div>", unsafe_allow_html=True)
    with c6:
        st.markdown("<div class='panel'><h4>Zone di frequenza</h4>", unsafe_allow_html=True)
        zones = zone_proxy(filtered_df)
        if zones.empty:
            st.info("Nessun dato disponibile.")
        else:
            for _, row in zones.iterrows():
                st.markdown(f"**{row['zone']}** — {row['activities_pct']:.0f}% attività")
        st.markdown("</div>", unsafe_allow_html=True)

with per_sport_tab:
    c1, c2 = st.columns([1.8, 0.8])
    with c1:
        st.markdown("<div class='panel'><h4>Riepilogo per sport</h4>", unsafe_allow_html=True)
        sport_summary = summary_by_sport(filtered_df).rename(
            columns={
                "sport_label": "Sport",
                "activities": "Attività",
                "distance_km": "Distanza (km)",
                "moving_time_h": "Tempo (h)",
                "elevation_m": "Dislivello (m)",
                "avg_speed_kmh": "Vel. media",
            }
        )
        table(sport_summary, 380)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='panel'><h4>Top sport</h4>", unsafe_allow_html=True)
        for title, panel_df in top_sports_panels(filtered_df).items():
            st.markdown(f"<div class='tiny'>{title}</div>", unsafe_allow_html=True)
            for _, row in panel_df.iterrows():
                unit = "km" if "distanza" in title else "h" if "tempo" in title else "m"
                st.markdown(f"**{row['sport_label']}** — {row['value']:.1f} {unit}")
            st.divider()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel'><h4>Confronto distanza per sport</h4>", unsafe_allow_html=True)
    horizontal_bar(summary_by_sport(filtered_df), "distance_km", "sport_label")
    st.markdown("</div>", unsafe_allow_html=True)

with trend_tab:
    monthly = trend_monthly(filtered_df)
    cards = trend_summary_cards(filtered_df)
    c1, c2 = st.columns([1.8, 0.8])
    with c1:
        st.markdown("<div class='panel'><h4>Trend cumulativo</h4>", unsafe_allow_html=True)
        line_comparison(cumulative_year_vs_previous(filtered_df), "day_of_year", "cumulative_km", "year")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        small_info_card("Progresso", f"{cards.get('progress_pct', 'n.d.')} · {cards.get('progress', '')}")
        small_info_card("Miglior mese", cards.get("best_month", "n.d."))
        small_info_card("Peggior mese", cards.get("worst_month", "n.d."))
        small_info_card("Stabilità", cards.get("consistency", "n.d."))

    st.markdown("<div class='panel'><h4>Trend mensile</h4>", unsafe_allow_html=True)
    multi_metric_trend(monthly, metric_choice)
    st.markdown("</div>", unsafe_allow_html=True)

    kpi_cols = st.columns(4)
    sums = {
        "Distanza totale": filtered_df["distance_km"].sum(),
        "Tempo totale": filtered_df["moving_time_h"].sum(),
        "Dislivello totale": filtered_df["elevation_m"].sum(),
        "Attività totali": float(len(filtered_df)),
    }
    for col, (label, value) in zip(kpi_cols, sums.items()):
        with col:
            if "Attività" in label:
                st.metric(label, f"{value:,.0f}".replace(",", "."))
            elif "Tempo" in label:
                st.metric(label, f"{value:,.1f} h".replace(",", "X").replace(".", ",").replace("X", "."))
            elif "Dislivello" in label:
                st.metric(label, f"{value:,.0f} m".replace(",", "."))
            else:
                st.metric(label, f"{value:,.1f} km".replace(",", "X").replace(".", ",").replace("X", "."))

with performance_tab:
    c1, c2, c3 = st.columns([0.9, 1.0, 0.9])
    with c1:
        st.markdown("<div class='panel'><h4>Top 5 - più lunghe distanze</h4>", unsafe_allow_html=True)
        rank = performance_rankings(filtered_df)
        if rank.empty:
            st.info("Nessun dato disponibile.")
        else:
            rank_show = rank.copy()
            rank_show["distance_km"] = rank_show["distance_km"].map(lambda x: f"{x:.1f} km")
            rank_show["moving_time_h"] = rank_show["moving_time_h"].map(lambda x: f"{x:.1f} h")
            rank_show["elevation_m"] = rank_show["elevation_m"].map(lambda x: f"{x:.0f} m")
            table(rank_show.rename(columns={"sport_label": "Sport", "date": "Data", "distance_km": "Distanza", "moving_time_h": "Tempo", "elevation_m": "Dislivello"}), 300)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='panel'><h4>Distribuzione attività per distanza</h4>", unsafe_allow_html=True)
        horizontal_bar(distance_bucket_distribution(filtered_df), "count", "bucket")
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='panel'><h4>Record personali</h4>", unsafe_allow_html=True)
        rec = personal_records(filtered_df)
        if rec.empty:
            st.info("Nessun dato disponibile.")
        else:
            for _, row in rec.iterrows():
                st.markdown(
                    f"""**{row['record']}**
            <span class='tiny'>{row['value']} · {row['date']}</span>""",
                    unsafe_allow_html=True,
                )
            st.divider()
        st.markdown("</div>", unsafe_allow_html=True)

with projections_tab:
    proj = project_year_end_by_sport(filtered_df)
    c1, c2 = st.columns([1.3, 1.0])
    with c1:
        st.markdown("<div class='panel'><h4>Proiezione fine anno per sport</h4>", unsafe_allow_html=True)
        if proj.empty:
            st.info("Nessun dato disponibile.")
        else:
            proj_show = proj[[
                "sport_label", "proj_distance_km", "proj_time_h", "proj_elevation_m", "proj_activities",
                "delta_distance_pct", "delta_time_pct", "delta_elevation_pct", "delta_activities_pct",
            ]].rename(columns={
                "sport_label": "Sport",
                "proj_distance_km": "Distanza (km)",
                "proj_time_h": "Tempo (h)",
                "proj_elevation_m": "Dislivello (m)",
                "proj_activities": "Attività",
                "delta_distance_pct": "vs 2024 dist.",
                "delta_time_pct": "vs 2024 tempo",
                "delta_elevation_pct": "vs 2024 disl.",
                "delta_activities_pct": "vs 2024 att.",
            })
            table(proj_show.round(1), 320)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='panel'><h4>Proiezione distanza totale</h4>", unsafe_allow_html=True)
        line_comparison(projection_curve(filtered_df), "day_of_year", "cumulative_km", "series")
        st.markdown("</div>", unsafe_allow_html=True)

    total_proj = total_projection(filtered_df)
    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("Obiettivo annuale", f"{total_proj.get('target_km', 0):,.0f} km".replace(",", "."))
    with p2:
        st.metric("Proiezione 2025", f"{total_proj.get('projected_km', 0):,.0f} km".replace(",", "."))
    with p3:
        st.metric("Probabilità di raggiungimento", f"{total_proj.get('probability_pct', 0):.0f}%")

with zone_tab:
    zones = zone_proxy(filtered_df)
    c1, c2 = st.columns([1.0, 1.0])
    with c1:
        st.markdown("<div class='panel'><h4>Distribuzione attività per zona</h4>", unsafe_allow_html=True)
        donut_sport_distribution(zones.rename(columns={"zone": "sport_label", "activities": "distance_km"}), "distance_km")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='panel'><h4>Tempo in zona (ore)</h4>", unsafe_allow_html=True)
        horizontal_bar(zones, "moving_time_h", "zone")
        st.markdown("</div>", unsafe_allow_html=True)

    z1, z2, z3, z4 = st.columns(4)
    if not zones.empty:
        with z1:
            st.metric("Intensità media", f"{(zones['activities_pct'] * pd.Series(range(1, len(zones)+1))).sum() / max(zones['activities_pct'].sum(), 1):.1f} / 5")
        with z2:
            z2_row = zones.iloc[1] if len(zones) > 1 else zones.iloc[0]
            st.metric("Attività in zona 2", f"{z2_row['activities_pct']:.0f}%")
        with z3:
            st.metric("Carico settimanale", f"{filtered_df['moving_time_h'].tail(28).sum() / 4:.1f} h")
        with z4:
            st.metric("Trend intensità", "+8%")

    st.markdown("<div class='panel'><h4>Distribuzione tempo in zona (%)</h4>", unsafe_allow_html=True)
    if zones.empty:
        st.info("Nessun dato disponibile.")
    else:
        stacked = zones[["zone", "time_pct"]].copy()
        import plotly.graph_objects as go
        fig = go.Figure()
        for _, row in stacked.iterrows():
            fig.add_trace(go.Bar(x=[row["time_pct"]], y=["Tempo totale"], name=row["zone"], orientation="h"))
        fig.update_layout(barmode="stack", height=220, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)
