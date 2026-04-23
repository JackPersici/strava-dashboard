from __future__ import annotations

import pandas as pd


def normalize_activities(raw: list[dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()

    df = pd.DataFrame(raw).copy()

    if "start_date_local" in df.columns:
        df["start_date_local"] = pd.to_datetime(df["start_date_local"], errors="coerce")

    if "distance" in df.columns:
        df["distance_km"] = df["distance"].fillna(0) / 1000

    if "moving_time" in df.columns:
        df["moving_time_h"] = df["moving_time"].fillna(0) / 3600

    if "total_elevation_gain" in df.columns:
        df["elevation_m"] = df["total_elevation_gain"].fillna(0)

    if "average_speed" in df.columns:
        df["avg_speed_kmh"] = df["average_speed"].fillna(0) * 3.6

    if "sport_type" not in df.columns and "type" in df.columns:
        df["sport_type"] = df["type"]

    if "id" not in df.columns:
        df["id"] = range(1, len(df) + 1)

    df["year"] = df["start_date_local"].dt.year
    df["month"] = df["start_date_local"].dt.to_period("M").astype(str)

    return df


def summary_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    out = (
        df.groupby("sport_type", dropna=False)
        .agg(
            activities=("id", "count"),
            distance_km=("distance_km", "sum"),
            moving_time_h=("moving_time_h", "sum"),
            elevation_m=("elevation_m", "sum"),
            avg_speed_kmh=("avg_speed_kmh", "mean"),
        )
        .reset_index()
        .sort_values(["distance_km", "moving_time_h"], ascending=False)
    )
    return out


def monthly_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    out = (
        df.groupby(["month", "sport_type"], dropna=False)
        .agg(
            distance_km=("distance_km", "sum"),
            moving_time_h=("moving_time_h", "sum"),
            elevation_m=("elevation_m", "sum"),
            activities=("id", "count"),
        )
        .reset_index()
    )
    return out
