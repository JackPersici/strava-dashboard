from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import streamlit as st


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    refresh_token: str
    scope: str
    activities_per_page: int = 100
    cache_file: str = "data/activities_modular.parquet"
    default_start_date: str = "2025-01-01"


def get_settings() -> Settings:
    return Settings(
        client_id=str(st.secrets["STRAVA_CLIENT_ID"]),
        client_secret=str(st.secrets["STRAVA_CLIENT_SECRET"]),
        refresh_token=str(st.secrets["STRAVA_REFRESH_TOKEN"]),
        scope=str(st.secrets.get("STRAVA_SCOPE", "read,activity:read_all")),
    )


def iso_to_unix(date_str: str) -> int:
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    return int(dt.timestamp())
