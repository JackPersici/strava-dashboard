from __future__ import annotations

from datetime import date
import numpy as np
import pandas as pd

SPORT_NAME_MAP = {
    "Ride": "Ciclismo",
    "VirtualRide": "VirtualRide",
    "GravelRide": "GravelRide",
    "Run": "Corsa",
    "TrailRun": "TrailRun",
    "Walk": "Camminata",
    "Hike": "Escursionismo",
    "AlpineSki": "Sci alpino",
    "BackcountrySki": "Sci alpinismo",
    "NordicSki": "Sci nordico",
    "Swim": "Nuoto",
    "StandUpPaddling": "SUP",
    "Surfing": "Surf",
    "Workout": "Workout",
}

ZONE_LABELS = [
    "Zona 1 (Recupero)",
    "Zona 2 (Endurance)",
    "Zona 3 (Tempo)",
    "Zona 4 (Soglia)",
    "Zona 5 (VO2 Max)",
]


def normalize_activities(raw: list[dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()

    df = pd.DataFrame(raw).copy()
    if "sport_type" not in df.columns and "type" in df.columns:
        df["sport_type"] = df["type"]

    df["sport_type"] = df["sport_type"].fillna("Altro")
    df["sport_label"] = df["sport_type"].map(SPORT_NAME_MAP).fillna(df["sport_type"])
    df["start_date_local"] = pd.to_datetime(df.get("start_date_local"), errors="coerce")
    df["distance_km"] = pd.to_numeric(df.get("distance"), errors="coerce").fillna(0) / 1000
    df["moving_time_h"] = pd.to_numeric(df.get("moving_time"), errors="coerce").fillna(0) / 3600
    df["elapsed_time_h"] = pd.to_numeric(df.get("elapsed_time"), errors="coerce").fillna(0) / 3600
    df["elevation_m"] = pd.to_numeric(df.get("total_elevation_gain"), errors="coerce").fillna(0)
    df["avg_speed_kmh"] = pd.to_numeric(df.get("average_speed"), errors="coerce").fillna(0) * 3.6
    df["max_speed_kmh"] = pd.to_numeric(df.get("max_speed"), errors="coerce").fillna(0) * 3.6
    df["suffer_score"] = pd.to_numeric(df.get("suffer_score"), errors="coerce").fillna(0)
    df["achievement_count"] = pd.to_numeric(df.get("achievement_count"), errors="coerce").fillna(0)
    df["commute"] = df.get("commute", False).fillna(False)
    df["trainer"] = df.get("trainer", False).fillna(False)
    df["manual"] = df.get("manual", False).fillna(False)
    df["month"] = df["start_date_local"].dt.to_period("M").astype(str)
    df["month_label"] = df["start_date_local"].dt.strftime("%b %Y")
    df["year"] = df["start_date_local"].dt.year
    df["week"] = df["start_date_local"].dt.isocalendar().week.astype("Int64")
    df["weekday_num"] = df["start_date_local"].dt.weekday
    df["weekday_name"] = df["start_date_local"].dt.day_name()
    df["day"] = df["start_date_local"].dt.date
    df["pace_min_km"] = np.where(df["distance_km"] > 0, (df["moving_time_h"] * 60) / df["distance_km"], np.nan)
    df["effort_score"] = (
        df["distance_km"] * 1.0
        + df["moving_time_h"] * 12.0
        + df["elevation_m"] / 150.0
        + df["achievement_count"] * 2.0
        + df["suffer_score"] / 8.0
    )
    return df.sort_values("start_date_local").reset_index(drop=True)


def available_sports(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []
    return sorted(df["sport_label"].dropna().unique().tolist())


def filter_activities(
    df: pd.DataFrame,
    sports: list[str] | None = None,
    year_mode: str = "Tutti gli anni",
) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    if sports and "Tutti gli sport" not in sports:
        out = out[out["sport_label"].isin(sports)]
    if year_mode == "Anno in corso":
        out = out[out["year"] == date.today().year]
    elif year_mode == "Anno scorso":
        out = out[out["year"] == date.today().year - 1]
    return out.sort_values("start_date_local")


def format_kpi_delta(current: float, previous: float, suffix: str = "") -> str:
    if previous <= 0:
        return "n.d."
    delta = ((current - previous) / previous) * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.0f}%{suffix}"


def compute_overview_kpis(filtered_df: pd.DataFrame, full_df: pd.DataFrame) -> dict[str, dict[str, str | float]]:
    if filtered_df.empty:
        return {}

    selected_years = sorted(filtered_df["year"].dropna().unique().tolist())
    focus_year = max(selected_years) if selected_years else date.today().year
    current = filtered_df[filtered_df["year"] == focus_year]
    prev = full_df[(full_df["year"] == focus_year - 1)]
    selected_sports = sorted(filtered_df["sport_label"].unique().tolist())
    if selected_sports:
        prev = prev[prev["sport_label"].isin(selected_sports)]

    current_cutoff = current["start_date_local"].max()
    if pd.notna(current_cutoff):
        prev = prev[prev["start_date_local"].dt.dayofyear <= int(current_cutoff.dayofyear)]

    metrics = {
        "Attività": (float(len(current)), float(len(prev))),
        "Distanza": (float(current["distance_km"].sum()), float(prev["distance_km"].sum())),
        "Tempo": (float(current["moving_time_h"].sum()), float(prev["moving_time_h"].sum())),
        "Dislivello": (float(current["elevation_m"].sum()), float(prev["elevation_m"].sum())),
    }
    out: dict[str, dict[str, str | float]] = {}
    for key, (cur, prv) in metrics.items():
        if key == "Attività":
            value = f"{cur:,.0f}".replace(",", ".")
        elif key == "Distanza":
            value = f"{cur:,.1f} km".replace(",", "X").replace(".", ",").replace("X", ".")
        elif key == "Tempo":
            value = f"{cur:,.1f} h".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            value = f"{cur:,.0f} m".replace(",", ".")
        out[key] = {"value": value, "delta": format_kpi_delta(cur, prv, " vs anno prec.")}
    return out


def monthly_distance_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby(["month", "sport_label"], as_index=False)
        .agg(distance_km=("distance_km", "sum"))
        .sort_values("month")
    )


def sport_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = (
        df.groupby("sport_label", as_index=False)
        .agg(distance_km=("distance_km", "sum"))
        .sort_values("distance_km", ascending=False)
    )
    total = out["distance_km"].sum()
    out["share"] = np.where(total > 0, out["distance_km"] / total * 100, 0)
    return out


def cumulative_year_vs_previous(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    years = sorted(df["year"].dropna().unique())
    focus_year = max(years)
    prev_year = focus_year - 1
    tmp = df[df["year"].isin([focus_year, prev_year])].copy()
    if tmp.empty:
        return pd.DataFrame()
    tmp["day_of_year"] = tmp["start_date_local"].dt.dayofyear
    grouped = (
        tmp.groupby(["year", "day_of_year"], as_index=False)
        .agg(distance_km=("distance_km", "sum"))
        .sort_values(["year", "day_of_year"])
    )
    grouped["cumulative_km"] = grouped.groupby("year")["distance_km"].cumsum()
    return grouped


def best_performances(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    picks = []
    for metric, label in [("distance_km", "Ride più lunga"), ("distance_km", "Run più lunga"), ("elevation_m", "Dislivello in una attività")]:
        if label.startswith("Ride"):
            tmp = df[df["sport_label"].isin(["Ciclismo", "VirtualRide", "GravelRide"])].nlargest(1, metric)
        elif label.startswith("Run"):
            tmp = df[df["sport_label"].isin(["Corsa", "TrailRun"])].nlargest(1, metric)
        else:
            tmp = df.nlargest(1, metric)
        if not tmp.empty:
            row = tmp.iloc[0]
            value = row[metric]
            if metric == "distance_km":
                value_text = f"{value:.1f} km"
            else:
                value_text = f"{value:,.0f} m".replace(",", ".")
            picks.append(
                {
                    "label": label,
                    "value": value_text,
                    "date": row["start_date_local"].strftime("%d %b %Y"),
                    "sport": row["sport_label"],
                }
            )
    return pd.DataFrame(picks)


def weekday_and_week_stats(df: pd.DataFrame) -> dict[str, str]:
    if df.empty:
        return {}
    day_counts = df.groupby("weekday_name").size().sort_values(ascending=False)
    preferred_day = day_counts.index[0]
    preferred_share = day_counts.iloc[0] / len(df) * 100

    tmp = df.copy()
    tmp["yearweek"] = tmp["start_date_local"].dt.strftime("%G-W%V")
    weekly = tmp.groupby("yearweek", as_index=False).agg(distance_km=("distance_km", "sum"), start=("start_date_local", "min"), end=("start_date_local", "max"))
    weekly = weekly.sort_values("distance_km", ascending=False)
    best_week = weekly.iloc[0]

    sport_dist = df.groupby("sport_label", as_index=False).agg(distance_km=("distance_km", "sum")).sort_values("distance_km", ascending=False)
    top_sport = sport_dist.iloc[0]
    total = sport_dist["distance_km"].sum()

    return {
        "preferred_day": f"{preferred_day} · {preferred_share:.0f}% delle attività",
        "best_week": f"{best_week['yearweek']} · {best_week['distance_km']:.0f} km",
        "top_sport": f"{top_sport['sport_label']} · {top_sport['distance_km'] / total * 100:.0f}% distanza",
    }


def summary_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = (
        df.groupby("sport_label", as_index=False)
        .agg(
            activities=("id", "count"),
            distance_km=("distance_km", "sum"),
            moving_time_h=("moving_time_h", "sum"),
            elevation_m=("elevation_m", "sum"),
            avg_speed_kmh=("avg_speed_kmh", "mean"),
        )
        .sort_values("distance_km", ascending=False)
    )
    return out


def top_sports_panels(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if df.empty:
        return {}
    return {
        "per distanza": df.groupby("sport_label", as_index=False).agg(value=("distance_km", "sum")).sort_values("value", ascending=False).head(3),
        "per tempo": df.groupby("sport_label", as_index=False).agg(value=("moving_time_h", "sum")).sort_values("value", ascending=False).head(3),
        "per dislivello": df.groupby("sport_label", as_index=False).agg(value=("elevation_m", "sum")).sort_values("value", ascending=False).head(3),
    }


def trend_monthly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.groupby(["month", "sport_label"], as_index=False).agg(
        distance_km=("distance_km", "sum"),
        moving_time_h=("moving_time_h", "sum"),
        elevation_m=("elevation_m", "sum"),
        activities=("id", "count"),
    )
    return out.sort_values("month")


def trend_summary_cards(df: pd.DataFrame) -> dict[str, str]:
    if df.empty:
        return {}
    monthly = df.groupby("month", as_index=False).agg(distance_km=("distance_km", "sum"))
    best = monthly.sort_values("distance_km", ascending=False).iloc[0]
    worst = monthly.sort_values("distance_km", ascending=True).iloc[0]
    progress = df["distance_km"].sum()
    target = max(3000.0, progress * 1.5)
    consistency = int(min(100, (df.groupby("month").size() > 0).mean() * 100))
    return {
        "progress": f"{progress:,.1f} km su {target:,.0f} km obiettivo".replace(",", "X").replace(".", ",").replace("X", "."),
        "progress_pct": f"{progress / target * 100:.0f}%",
        "best_month": f"{best['month']} · {best['distance_km']:.1f} km",
        "worst_month": f"{worst['month']} · {worst['distance_km']:.1f} km",
        "consistency": f"Indice di costanza {consistency}/100",
    }


def performance_rankings(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.nlargest(5, "distance_km")[["sport_label", "start_date_local", "distance_km", "moving_time_h", "elevation_m"]].copy()
    out["date"] = out["start_date_local"].dt.strftime("%d %b %Y")
    return out[["sport_label", "date", "distance_km", "moving_time_h", "elevation_m"]]


def distance_bucket_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    bins = [-1, 10, 25, 50, 100, 10_000]
    labels = ["<10 km", "10-25 km", "25-50 km", "50-100 km", ">100 km"]
    tmp = df.copy()
    tmp["bucket"] = pd.cut(tmp["distance_km"], bins=bins, labels=labels)
    out = tmp.groupby("bucket", observed=False, as_index=False).agg(count=("id", "count"))
    out["bucket"] = out["bucket"].astype(str)
    return out


def personal_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    records = []
    longest = df.nlargest(1, "distance_km").iloc[0]
    longest_time = df.nlargest(1, "moving_time_h").iloc[0]
    highest_elev = df.nlargest(1, "elevation_m").iloc[0]
    top_speed = df.nlargest(1, "avg_speed_kmh").iloc[0]
    records.extend(
        [
            {"record": "Distanza più lunga", "value": f"{longest['distance_km']:.1f} km", "date": longest['start_date_local'].strftime("%d %b %Y")},
            {"record": "Tempo più lungo", "value": f"{longest_time['moving_time_h']:.1f} h", "date": longest_time['start_date_local'].strftime("%d %b %Y")},
            {"record": "Dislivello più alto", "value": f"{highest_elev['elevation_m']:.0f} m", "date": highest_elev['start_date_local'].strftime("%d %b %Y")},
            {"record": "Velocità media più alta", "value": f"{top_speed['avg_speed_kmh']:.1f} km/h", "date": top_speed['start_date_local'].strftime("%d %b %Y")},
        ]
    )
    return pd.DataFrame(records)


def zone_proxy(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    tmp = df.copy()
    tmp["effort_rank"] = tmp.groupby("sport_label")["effort_score"].rank(pct=True)
    bins = [0.0, 0.2, 0.5, 0.75, 0.9, 1.0]
    tmp["zone"] = pd.cut(tmp["effort_rank"], bins=bins, labels=ZONE_LABELS, include_lowest=True)
    out = tmp.groupby("zone", observed=False, as_index=False).agg(
        activities=("id", "count"),
        moving_time_h=("moving_time_h", "sum"),
    )
    out["zone"] = out["zone"].astype(str)
    total_acts = out["activities"].sum()
    total_time = out["moving_time_h"].sum()
    out["activities_pct"] = np.where(total_acts > 0, out["activities"] / total_acts * 100, 0)
    out["time_pct"] = np.where(total_time > 0, out["moving_time_h"] / total_time * 100, 0)
    return out
