from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import streamlit as st


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    refresh_token: str
    scope: str
    activities_per_page: int = 100
    cache_file: str = "data/activities.parquet"
    default_start_date: str = "2025-01-01"


def get_secret(name: str, default: str = "") -> str:
    try:
        value: Any = st.secrets[name]
        return str(value)
    except Exception:
        return default


def has_required_secrets() -> bool:
    return all([
        get_secret("STRAVA_CLIENT_ID"),
        get_secret("STRAVA_CLIENT_SECRET"),
        get_secret("STRAVA_REFRESH_TOKEN"),
    ])


def get_settings() -> Settings:
    return Settings(
        client_id=get_secret("STRAVA_CLIENT_ID"),
        client_secret=get_secret("STRAVA_CLIENT_SECRET"),
        refresh_token=get_secret("STRAVA_REFRESH_TOKEN"),
        scope=get_secret("STRAVA_SCOPE", "read,activity:read_all"),
    )


def iso_to_unix(date_str: str) -> int:
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def secrets_file_path() -> Path:
    return Path(".streamlit") / "secrets.toml"


def write_secrets_file(client_id: str, client_secret: str, refresh_token: str, scope: str = "read,activity:read_all") -> Path:
    p = secrets_file_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f'STRAVA_CLIENT_ID = "{client_id}"\n'
        f'STRAVA_CLIENT_SECRET = "{client_secret}"\n'
        f'STRAVA_REFRESH_TOKEN = "{refresh_token}"\n'
        f'STRAVA_SCOPE = "{scope}"\n'
    )
    p.write_text(content, encoding="utf-8")
    return p
