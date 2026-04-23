from __future__ import annotations

from datetime import date
import streamlit as st

from app.config import get_settings, has_required_secrets, iso_to_unix, write_secrets_file
from app.metrics import normalize_activities, summary_by_sport, monthly_by_sport
from app.projections import project_year_end_by_sport
from app.storage import load_activities, save_activities
from app.strava_api import StravaClient
from app.ui import show_kpis, show_monthly_chart, show_projection_chart


st.set_page_config(
    page_title="Strava Dashboard",
    page_icon=":bike:",
    layout="wide",
)

st.title("Strava Dashboard")
st.caption("Responsive per iPhone e PC")

if not has_required_secrets():
    st.warning("Mancano i dati Strava. Inseriscili una volta sola qui sotto.")
    with st.form("setup_secrets"):
        client_id = st.text_input("STRAVA_CLIENT_ID")
        client_secret = st.text_input("STRAVA_CLIENT_SECRET", type="password")
        refresh_token = st.text_input("STRAVA_REFRESH_TOKEN", type="password")
        submitted = st.form_submit_button("Salva e ricarica")

    if submitted:
        if client_id and client_secret and refresh_token:
            p = write_secrets_file(client_id, client_secret, refresh_token)
            st.success(f"Segreti salvati in {p}. Ora ricarico l'app.")
            st.rerun()
        else:
            st.error("Compila tutti i campi.")
    st.stop()

settings = get_settings()
client = StravaClient(settings)

with st.expander("Filtri e sincronizzazione", expanded=True):
    default_start = settings.default_start_date
    start_date = st.date_input("Importa attivita da", value=date.fromisoformat(default_start))
    sync_now = st.button("Sincronizza da Strava")

if sync_now:
    try:
        with st.spinner("Scarico le attivita da Strava..."):
            after_ts = iso_to_unix(start_date.isoformat())
            raw = client.list_activities(after_ts=after_ts)
            df = normalize_activities(raw)
            save_activities(df, settings.cache_file)
            st.success(f"Sincronizzazione completata: {len(df)} attivita.")
    except Exception as e:
        st.error(f"Errore durante la sincronizzazione: {e}")


df = load_activities(settings.cache_file)

if df.empty:
    st.info("Nessun dato disponibile per ora. Premi 'Sincronizza da Strava'.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Overview", "Per sport", "Proiezioni"])

with tab1:
    show_kpis(df)
    monthly = monthly_by_sport(df)
    show_monthly_chart(monthly)

with tab2:
    sport_summary = summary_by_sport(df)
    st.subheader("Riepilogo per sport")
    st.dataframe(
        sport_summary,
        use_container_width=True,
        hide_index=True,
    )

with tab3:
    proj = project_year_end_by_sport(df)
    st.subheader("Proiezione fine anno")
    st.dataframe(proj, use_container_width=True, hide_index=True)
    show_projection_chart(proj)
