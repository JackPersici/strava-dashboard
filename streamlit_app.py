from __future__ import annotations

from datetime import date
import streamlit as st

from app.config import get_settings, iso_to_unix
from app.metrics import normalize_activities, summary_by_sport, monthly_by_sport
from app.projections import project_year_end_by_sport
from app.storage import load_activities, save_activities
from app.strava_api import StravaClient
from app.ui import show_kpis, show_monthly_chart, show_projection_chart


st.set_page_config(
    page_title="Strava Dashboard",
    page_icon="🚴",
    layout="wide",
)

st.markdown(
    """
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="Strava Dashboard">
    <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/747/747376.png">
    """,
    unsafe_allow_html=True,
)

try:
    settings = get_settings()
except Exception:
    st.title("Strava Dashboard")
    st.error("Secrets mancanti o non validi.")
    st.info(
        "Su Streamlit Cloud inserisci i secrets da: Manage app -> Settings -> Secrets."
    )
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
st.caption("Responsive per iPhone e PC")

with st.expander("Filtri e sincronizzazione", expanded=True):
    default_start = settings.default_start_date
    start_date = st.date_input("Importa attività da", value=date.fromisoformat(default_start))
    sync_now = st.button("Sincronizza da Strava")

if sync_now:
    try:
        with st.spinner("Scarico le attività da Strava..."):
            after_ts = iso_to_unix(start_date.isoformat())
            raw = client.list_activities(after_ts=after_ts)
            df = normalize_activities(raw)
            save_activities(df, settings.cache_file)
            st.success(f"Sincronizzazione completata: {len(df)} attività.")
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
        width="stretch",
        hide_index=True,
    )

with tab3:
    proj = project_year_end_by_sport(df)
    st.subheader("Proiezione fine anno")
    st.dataframe(proj, width="stretch", hide_index=True)
    show_projection_chart(proj)
