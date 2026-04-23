from __future__ import annotations

from datetime import date
import pandas as pd


def project_year_end_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    today = date.today()
    start_of_year = date(today.year, 1, 1)
    end_of_year = date(today.year, 12, 31)

    elapsed_days = (today - start_of_year).days + 1
    total_days = (end_of_year - start_of_year).days + 1

    current_year = df[df["year"] == today.year].copy()
    if current_year.empty:
        return pd.DataFrame()

    grouped = (
        current_year.groupby("sport_type", dropna=False)
        .agg(
            ytd_distance_km=("distance_km", "sum"),
            ytd_time_h=("moving_time_h", "sum"),
            ytd_elevation_m=("elevation_m", "sum"),
            ytd_activities=("id", "count"),
        )
        .reset_index()
    )

    grouped["proj_distance_km"] = grouped["ytd_distance_km"] / elapsed_days * total_days
    grouped["proj_time_h"] = grouped["ytd_time_h"] / elapsed_days * total_days
    grouped["proj_elevation_m"] = grouped["ytd_elevation_m"] / elapsed_days * total_days
    grouped["proj_activities"] = grouped["ytd_activities"] / elapsed_days * total_days

    return grouped.sort_values("proj_distance_km", ascending=False)
