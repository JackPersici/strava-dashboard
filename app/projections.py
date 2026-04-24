from __future__ import annotations

from datetime import date
import pandas as pd


def project_year_end_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    today = date.today()
    current_year = today.year
    start_of_year = date(current_year, 1, 1)
    end_of_year = date(current_year, 12, 31)
    elapsed_days = (today - start_of_year).days + 1
    total_days = (end_of_year - start_of_year).days + 1

    current = df[df["year"] == current_year].copy()
    previous = df[df["year"] == current_year - 1].copy()
    if current.empty:
        return pd.DataFrame()

    cur = (
        current.groupby("sport_label", as_index=False)
        .agg(
            ytd_distance_km=("distance_km", "sum"),
            ytd_time_h=("moving_time_h", "sum"),
            ytd_elevation_m=("elevation_m", "sum"),
            ytd_activities=("id", "count"),
        )
    )
    cur["proj_distance_km"] = cur["ytd_distance_km"] / elapsed_days * total_days
    cur["proj_time_h"] = cur["ytd_time_h"] / elapsed_days * total_days
    cur["proj_elevation_m"] = cur["ytd_elevation_m"] / elapsed_days * total_days
    cur["proj_activities"] = cur["ytd_activities"] / elapsed_days * total_days

    prev = previous.groupby("sport_label", as_index=False).agg(
        prev_distance_km=("distance_km", "sum"),
        prev_time_h=("moving_time_h", "sum"),
        prev_elevation_m=("elevation_m", "sum"),
        prev_activities=("id", "count"),
    )

    out = cur.merge(prev, on="sport_label", how="left").fillna(0)
    out["delta_distance_pct"] = ((out["proj_distance_km"] - out["prev_distance_km"]) / out["prev_distance_km"].replace(0, pd.NA) * 100).fillna(0)
    out["delta_time_pct"] = ((out["proj_time_h"] - out["prev_time_h"]) / out["prev_time_h"].replace(0, pd.NA) * 100).fillna(0)
    out["delta_elevation_pct"] = ((out["proj_elevation_m"] - out["prev_elevation_m"]) / out["prev_elevation_m"].replace(0, pd.NA) * 100).fillna(0)
    out["delta_activities_pct"] = ((out["proj_activities"] - out["prev_activities"]) / out["prev_activities"].replace(0, pd.NA) * 100).fillna(0)
    return out.sort_values("proj_distance_km", ascending=False)


def total_projection(df: pd.DataFrame) -> dict[str, float]:
    proj = project_year_end_by_sport(df)
    if proj.empty:
        return {}
    total_proj = proj["proj_distance_km"].sum()
    current = proj["ytd_distance_km"].sum()
    target = max(3300.0, current * 1.2)
    probability = min(100.0, max(0.0, total_proj / target * 100))
    return {
        "target_km": target,
        "projected_km": total_proj,
        "probability_pct": probability,
    }


def projection_curve(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    current_year = date.today().year
    previous_year = current_year - 1
    tmp = df[df["year"].isin([current_year, previous_year])].copy()
    if tmp.empty:
        return pd.DataFrame()
    tmp["day_of_year"] = tmp["start_date_local"].dt.dayofyear
    grouped = tmp.groupby(["year", "day_of_year"], as_index=False).agg(distance_km=("distance_km", "sum"))
    grouped["cumulative_km"] = grouped.groupby("year")["distance_km"].cumsum()
    grouped["series"] = grouped["year"].astype(str)
    return grouped.sort_values(["year", "day_of_year"])
