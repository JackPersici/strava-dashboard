from __future__ import annotations

from datetime import date
from typing import Iterable

import numpy as np
import pandas as pd


SPORT_MAP = {
    "Ride": "Ciclismo",
    "VirtualRide": "VirtualRide",
    "GravelRide": "GravelRide",
    "EBikeRide": "E-Bike",
    "Run": "Corsa",
    "TrailRun": "TrailRun",
    "Walk": "Camminata",
    "Hike": "Escursionismo",
    "AlpineSki": "Sci alpino",
    "BackcountrySki": "Sci alpinismo",
    "NordicSki": "Sci nordico",
    "Swim": "Nuoto",
    "Workout": "Workout",
    "StandUpPaddling": "SUP",
    "Surfing": "Surf",
    "Rowing": "Canottaggio",
    "WeightTraining": "Pesi",
    "Yoga": "Yoga",
}
MONTH_MAP = {
    1: "Gen", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mag", 6: "Giu",
    7: "Lug", 8: "Ago", 9: "Set", 10: "Ott", 11: "Nov", 12: "Dic",
}
MONTH_ORDER = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]


def _empty_series(df: pd.DataFrame, default: float = 0.0) -> pd.Series:
    return pd.Series([default] * len(df), index=df.index, dtype="float64")


def _numeric_col(df: pd.DataFrame, col_name: str, default: float = 0.0) -> pd.Series:
    if col_name in df.columns:
        return pd.to_numeric(df[col_name], errors="coerce").fillna(default)
    return _empty_series(df, default=default)


def normalize_activities(raw: list[dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()

    df = pd.DataFrame(raw).copy()

    if "start_date_local" in df.columns:
        df["start_date_local"] = pd.to_datetime(df["start_date_local"], errors="coerce")
    elif "start_date" in df.columns:
        df["start_date_local"] = pd.to_datetime(df["start_date"], errors="coerce")
    else:
        df["start_date_local"] = pd.NaT

    if "sport_type" not in df.columns:
        df["sport_type"] = df["type"] if "type" in df.columns else "Other"

    if "name" not in df.columns:
        df["name"] = "Attività"

    df["distance"] = _numeric_col(df, "distance")
    df["moving_time"] = _numeric_col(df, "moving_time")
    df["elapsed_time"] = _numeric_col(df, "elapsed_time")
    df["total_elevation_gain"] = _numeric_col(df, "total_elevation_gain")
    df["average_speed"] = _numeric_col(df, "average_speed")
    df["max_speed"] = _numeric_col(df, "max_speed")
    df["average_heartrate"] = _numeric_col(df, "average_heartrate")
    df["max_heartrate"] = _numeric_col(df, "max_heartrate")
    df["average_watts"] = _numeric_col(df, "average_watts")
    df["kilojoules"] = _numeric_col(df, "kilojoules")
    df["suffer_score"] = _numeric_col(df, "suffer_score")

    if "id" not in df.columns:
        df["id"] = range(1, len(df) + 1)

    for col in ["trainer", "commute", "manual"]:
        if col not in df.columns:
            df[col] = False
        df[col] = df[col].fillna(False).astype(bool)

    df["distance_km"] = df["distance"] / 1000.0
    df["moving_time_h"] = df["moving_time"] / 3600.0
    df["elapsed_time_h"] = df["elapsed_time"] / 3600.0
    df["elevation_m"] = df["total_elevation_gain"]
    df["avg_speed_kmh"] = df["average_speed"] * 3.6
    df["max_speed_kmh"] = df["max_speed"] * 3.6
    df["pace_min_km"] = np.where(
        df["distance_km"] > 0,
        (df["moving_time"] / 60.0) / df["distance_km"],
        np.nan,
    )

    df["year"] = df["start_date_local"].dt.year
    df["month_num"] = df["start_date_local"].dt.month
    df["month"] = df["month_num"].map(MONTH_MAP)
    df["month_year"] = df["start_date_local"].dt.to_period("M").astype(str)
    df["week"] = df["start_date_local"].dt.isocalendar().week.astype("Int64")
    df["weekday_num"] = df["start_date_local"].dt.weekday
    df["weekday"] = df["start_date_local"].dt.day_name()
    df["day"] = df["start_date_local"].dt.date

    df["sport_label"] = df["sport_type"].map(SPORT_MAP).fillna(df["sport_type"])

    df["effort_score"] = (
        df["distance_km"] * 1.2
        + df["moving_time_h"] * 12
        + df["elevation_m"] / 250.0
        + df["average_heartrate"] / 18.0
        + df["average_watts"] / 35.0
    ).fillna(0)

    return df


def filter_activities(
    df: pd.DataFrame,
    selected_sports: Iterable[str] | None = None,
    years: Iterable[int] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()
    if selected_sports:
        out = out[out["sport_label"].isin(list(selected_sports))]
    if years:
        out = out[out["year"].isin(list(years))]
    return out


def available_sports(df: pd.DataFrame) -> list[str]:
    if df.empty or "sport_label" not in df.columns:
        return []
    return sorted(df["sport_label"].dropna().astype(str).unique().tolist())


def group_small_sports(df: pd.DataFrame, threshold_pct: float = 5.0, min_activities: int = 3, top_n: int = 5) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    temp = df.copy()
    total_distance = float(temp["distance_km"].sum())
    if total_distance <= 0:
        temp["sport_grouped"] = temp["sport_label"].fillna("Altri")
        return temp

    summary = (
        temp.groupby("sport_label", dropna=False)
        .agg(distance_km=("distance_km", "sum"), activities=("id", "count"))
        .reset_index()
        .sort_values("distance_km", ascending=False)
    )
    summary["pct"] = (summary["distance_km"] / total_distance) * 100.0
    top_sports = summary.head(top_n)["sport_label"].tolist()

    def mapped(row: pd.Series) -> str:
        if row["sport_label"] not in top_sports or row["pct"] < threshold_pct or row["activities"] < min_activities:
            return "Altri"
        return str(row["sport_label"])

    mapping = {row["sport_label"]: mapped(row) for _, row in summary.iterrows()}
    temp["sport_grouped"] = temp["sport_label"].map(mapping).fillna("Altri")
    return temp


def _sport_col(df: pd.DataFrame) -> str:
    return "sport_grouped" if "sport_grouped" in df.columns else "sport_label"


def kpi_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "activities": 0,
            "distance_km": 0.0,
            "moving_time_h": 0.0,
            "elevation_m": 0.0,
            "avg_distance_km": 0.0,
            "avg_time_h": 0.0,
            "avg_elevation_m": 0.0,
        }

    return {
        "activities": int(df["id"].count()),
        "distance_km": float(df["distance_km"].sum()),
        "moving_time_h": float(df["moving_time_h"].sum()),
        "elevation_m": float(df["elevation_m"].sum()),
        "avg_distance_km": float(df["distance_km"].mean()),
        "avg_time_h": float(df["moving_time_h"].mean()),
        "avg_elevation_m": float(df["elevation_m"].mean()),
    }


def summary_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    sport_col = _sport_col(df)
    out = (
        df.groupby(sport_col, dropna=False)
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
    return out.rename(columns={sport_col: "sport_grouped"})


def monthly_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    sport_col = _sport_col(df)
    out = (
        df.groupby(["year", "month_num", "month", sport_col], dropna=False)
        .agg(
            distance_km=("distance_km", "sum"),
            moving_time_h=("moving_time_h", "sum"),
            elevation_m=("elevation_m", "sum"),
            activities=("id", "count"),
        )
        .reset_index()
        .sort_values(["year", "month_num"])
    )
    return out.rename(columns={sport_col: "sport_grouped"})


def cumulative_by_year(df: pd.DataFrame, metric: str = "distance_km") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    temp = (
        df.groupby(["year", "month_num"], dropna=False)[metric]
        .sum()
        .reset_index()
        .sort_values(["year", "month_num"])
    )
    temp["cumulative"] = temp.groupby("year")[metric].cumsum()
    temp["month_label"] = temp["month_num"].map(MONTH_MAP)
    return temp


def trend_monthly(df: pd.DataFrame, metric: str = "distance_km") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    out = (
        df.groupby(["year", "month_num"], dropna=False)[metric]
        .sum()
        .reset_index()
    )
    all_months = pd.DataFrame({"month_num": list(range(1, 13))})

    result: list[pd.DataFrame] = []
    for year in out["year"].dropna().unique().tolist():
        temp = out[out["year"] == year]
        merged = all_months.merge(temp, on="month_num", how="left")
        merged["year"] = year
        merged[metric] = merged[metric].fillna(0)
        result.append(merged)

    final = pd.concat(result, ignore_index=True) if result else pd.DataFrame()
    if final.empty:
        return final

    final["month"] = final["month_num"].map(MONTH_MAP)
    return final.sort_values(["year", "month_num"])


def compare_vs_previous_year(df: pd.DataFrame, metric: str = "distance_km") -> dict:
    if df.empty or df["year"].dropna().empty:
        return {"current": 0.0, "previous": 0.0, "delta_pct": 0.0, "current_year": date.today().year, "previous_year": date.today().year - 1}

    current_year = int(df["year"].max())
    previous_year = current_year - 1
    current_total = float(df.loc[df["year"] == current_year, metric].sum())
    prev_total = float(df.loc[df["year"] == previous_year, metric].sum())

    if prev_total == 0:
        delta_pct = 100.0 if current_total > 0 else 0.0
    else:
        delta_pct = ((current_total - prev_total) / prev_total) * 100.0

    return {
        "current": current_total,
        "previous": prev_total,
        "delta_pct": delta_pct,
        "current_year": current_year,
        "previous_year": previous_year,
    }


def best_performances(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows: list[dict] = []

    def add_best(frame: pd.DataFrame, label: str, formatter) -> None:
        if frame.empty:
            return
        r = frame.iloc[0]
        rows.append({
            "label": label,
            "value": formatter(r),
            "date": pd.to_datetime(r["start_date_local"]).strftime("%d %b %Y"),
            "sport": r.get("sport_grouped", r["sport_label"]),
        })

    add_best(df.sort_values("distance_km", ascending=False).head(1), "Distanza più lunga", lambda r: f"{r['distance_km']:.1f} km")
    run_df = df[df["sport_type"].isin(["Run", "TrailRun"])].sort_values("distance_km", ascending=False).head(1)
    add_best(run_df, "Run più lunga", lambda r: f"{r['distance_km']:.1f} km")
    add_best(df.sort_values("elevation_m", ascending=False).head(1), "Dislivello in una attività", lambda r: f"{r['elevation_m']:.0f} m")
    add_best(df.sort_values("moving_time_h", ascending=False).head(1), "Tempo più lungo", lambda r: f"{r['moving_time_h']:.1f} h")
    return pd.DataFrame(rows)


def favorite_weekday(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"weekday": "-", "pct": 0.0}
    counts = df["weekday"].value_counts(dropna=True)
    if counts.empty:
        return {"weekday": "-", "pct": 0.0}
    return {"weekday": str(counts.index[0]), "pct": float(counts.iloc[0] / len(df) * 100.0)}


def most_active_week(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"week": "-", "activities": 0}
    temp = (
        df.dropna(subset=["year", "week"])
        .groupby(["year", "week"])
        .size()
        .reset_index(name="activities")
        .sort_values("activities", ascending=False)
    )
    if temp.empty:
        return {"week": "-", "activities": 0}
    r = temp.iloc[0]
    return {"week": f"Settimana {int(r['week'])}", "activities": int(r["activities"]), "year": int(r["year"])}


def primary_sport(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"sport": "-", "pct": 0.0}
    sport_col = _sport_col(df)
    temp = df.groupby(sport_col)["distance_km"].sum().sort_values(ascending=False)
    if temp.empty:
        return {"sport": "-", "pct": 0.0}
    total = float(temp.sum())
    return {"sport": str(temp.index[0]), "pct": float((temp.iloc[0] / total) * 100.0) if total > 0 else 0.0}


def distance_bucket_distribution(df: pd.DataFrame, mode: str = "count", bucket_col: str = "bucket") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    bins = [-0.001, 10, 25, 50, 100, float("inf")]
    labels = ["<10 km", "10-25 km", "25-50 km", "50-100 km", ">100 km"]
    temp = df.copy()
    temp[bucket_col] = pd.cut(temp["distance_km"], bins=bins, labels=labels)
    if mode == "count":
        out = temp.groupby(bucket_col, observed=False).size().reset_index(name="count")
    else:
        out = temp.groupby(bucket_col, observed=False)["distance_km"].sum().reset_index(name="count")
    return out


def personal_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows: list[dict] = []

    def add_record(frame: pd.DataFrame, record: str, formatter) -> None:
        if frame.empty:
            return
        r = frame.iloc[0]
        rows.append({
            "record": record,
            "value": formatter(r),
            "date": pd.to_datetime(r["start_date_local"]).strftime("%d %b %Y"),
        })

    add_record(df.sort_values("distance_km", ascending=False).head(1), "Distanza più lunga", lambda r: f"{r['distance_km']:.1f} km")
    add_record(df.sort_values("moving_time_h", ascending=False).head(1), "Tempo più lungo", lambda r: f"{r['moving_time_h']:.1f} h")
    add_record(df.sort_values("elevation_m", ascending=False).head(1), "Dislivello più alto", lambda r: f"{r['elevation_m']:.0f} m")
    add_record(df.sort_values("avg_speed_kmh", ascending=False).head(1), "Velocità media più alta", lambda r: f"{r['avg_speed_kmh']:.1f} km/h")
    return pd.DataFrame(rows)


def zone_proxy(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    temp = df.copy()

    def zone_name(v: float) -> str:
        if v < 15:
            return "Zona 1 (Recupero)"
        if v < 30:
            return "Zona 2 (Endurance)"
        if v < 50:
            return "Zona 3 (Tempo)"
        if v < 75:
            return "Zona 4 (Soglia)"
        return "Zona 5 (VO2 Max)"

    temp["zone"] = temp["effort_score"].fillna(0).map(zone_name)
    out = (
        temp.groupby("zone", dropna=False)
        .agg(activities=("id", "count"), moving_time_h=("moving_time_h", "sum"))
        .reset_index()
    )
    order = ["Zona 1 (Recupero)", "Zona 2 (Endurance)", "Zona 3 (Tempo)", "Zona 4 (Soglia)", "Zona 5 (VO2 Max)"]
    out["zone"] = pd.Categorical(out["zone"], categories=order, ordered=True)
    out = out.sort_values("zone").reset_index(drop=True)
    total_activities = out["activities"].sum()
    total_time = out["moving_time_h"].sum()
    out["activities_pct"] = np.where(total_activities > 0, (out["activities"] / total_activities) * 100.0, 0.0)
    out["time_pct"] = np.where(total_time > 0, (out["moving_time_h"] / total_time) * 100.0, 0.0)
    return out


def monthly_best_worst(df: pd.DataFrame, metric: str = "distance_km") -> dict:
    if df.empty:
        return {"best_month": "-", "best_value": 0.0, "worst_month": "-", "worst_value": 0.0}
    temp = (
        df.groupby(["month_num", "month"])[metric]
        .sum()
        .reset_index()
        .sort_values(metric, ascending=False)
    )
    if temp.empty:
        return {"best_month": "-", "best_value": 0.0, "worst_month": "-", "worst_value": 0.0}
    best = temp.iloc[0]
    worst = temp.iloc[-1]
    return {
        "best_month": str(best["month"]),
        "best_value": float(best[metric]),
        "worst_month": str(worst["month"]),
        "worst_value": float(worst[metric]),
    }


def consistency_score(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    temp = (
        df.dropna(subset=["year", "week"])
        .groupby(["year", "week"])
        .size()
        .reset_index(name="activities")
    )
    if temp.empty:
        return 0.0
    active_weeks = int((temp["activities"] > 0).sum())
    total_weeks = int(temp.shape[0])
    return round((active_weeks / total_weeks) * 100.0, 1) if total_weeks > 0 else 0.0


def current_year_projection(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or df["year"].dropna().empty:
        return pd.DataFrame()

    sport_col = _sport_col(df)
    today = date.today()
    current_year = today.year
    current_df = df[df["year"] == current_year].copy()
    if current_df.empty:
        return pd.DataFrame()

    start_of_year = date(current_year, 1, 1)
    end_of_year = date(current_year, 12, 31)
    elapsed_days = (today - start_of_year).days + 1
    total_days = (end_of_year - start_of_year).days + 1

    proj = (
        current_df.groupby(sport_col, dropna=False)
        .agg(
            ytd_distance_km=("distance_km", "sum"),
            ytd_time_h=("moving_time_h", "sum"),
            ytd_elevation_m=("elevation_m", "sum"),
            ytd_activities=("id", "count"),
        )
        .reset_index()
    )
    proj["proj_distance_km"] = proj["ytd_distance_km"] / elapsed_days * total_days
    proj["proj_time_h"] = proj["ytd_time_h"] / elapsed_days * total_days
    proj["proj_elevation_m"] = proj["ytd_elevation_m"] / elapsed_days * total_days
    proj["proj_activities"] = proj["ytd_activities"] / elapsed_days * total_days

    prev = (
        df[df["year"] == current_year - 1]
        .groupby(sport_col, dropna=False)
        .agg(
            prev_distance_km=("distance_km", "sum"),
            prev_time_h=("moving_time_h", "sum"),
            prev_elevation_m=("elevation_m", "sum"),
            prev_activities=("id", "count"),
        )
        .reset_index()
    )
    proj = proj.merge(prev, on=sport_col, how="left").fillna(0)

    def pct(a: pd.Series, b: pd.Series) -> pd.Series:
        return ((a - b) / b.replace(0, pd.NA) * 100).fillna(0)

    proj["delta_distance_pct"] = pct(proj["proj_distance_km"], proj["prev_distance_km"])
    proj["delta_time_pct"] = pct(proj["proj_time_h"], proj["prev_time_h"])
    proj["delta_elevation_pct"] = pct(proj["proj_elevation_m"], proj["prev_elevation_m"])
    proj["delta_activities_pct"] = pct(proj["proj_activities"], proj["prev_activities"])
    return proj.rename(columns={sport_col: "sport_grouped"}).sort_values("proj_distance_km", ascending=False).reset_index(drop=True)


def top_sports_panels(sport_df: pd.DataFrame) -> dict:
    if sport_df.empty:
        return {"distance": [], "time": [], "elevation": []}

    return {
        "distance": sport_df.sort_values("distance_km", ascending=False)[["sport_grouped", "distance_km"]].head(3).rename(columns={"sport_grouped": "sport_label"}).to_dict("records"),
        "time": sport_df.sort_values("moving_time_h", ascending=False)[["sport_grouped", "moving_time_h"]].head(3).rename(columns={"sport_grouped": "sport_label"}).to_dict("records"),
        "elevation": sport_df.sort_values("elevation_m", ascending=False)[["sport_grouped", "elevation_m"]].head(3).rename(columns={"sport_grouped": "sport_label"}).to_dict("records"),
    }
