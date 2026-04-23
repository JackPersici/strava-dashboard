from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def show_kpis(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Nessuna attivita caricata.")
        return

    total_activities = int(df["id"].count())
    total_distance = float(df["distance_km"].sum())
    total_hours = float(df["moving_time_h"].sum())
    total_elevation = float(df["elevation_m"].sum())

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    c1.metric("Attivita", f"{total_activities}")
    c2.metric("Distanza", f"{total_distance:,.1f} km")
    c3.metric("Tempo", f"{total_hours:,.1f} h")
    c4.metric("Dislivello", f"{total_elevation:,.0f} m")


def show_monthly_chart(monthly_df: pd.DataFrame) -> None:
    if monthly_df.empty:
        return

    fig = px.bar(
        monthly_df,
        x="month",
        y="distance_km",
        color="sport_type",
        barmode="group",
        title="Distanza mensile per sport",
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)


def show_projection_chart(proj_df: pd.DataFrame) -> None:
    if proj_df.empty:
        return

    fig = px.bar(
        proj_df,
        x="sport_type",
        y="proj_distance_km",
        title="Proiezione distanza a fine anno",
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)
