from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


MONTH_MAP = {
    1: "Gen", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mag", 6: "Giu",
    7: "Lug", 8: "Ago", 9: "Set", 10: "Ott", 11: "Nov", 12: "Dic",
}

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


def _empty_series(df: pd.DataFrame, default: float = 0.0) -> pd.Series:
    return pd.Series([default] * len(df), index=df.index, dtype="float64")


def _numeric_col(df: pd.DataFrame, col_name: str, default: float = 0.0) -> pd.Series:
    if col_name in df.columns:
        return pd.to_numeric(df[col_name], errors="coerce").fillna(default)
    return _empty_series(df, default)


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

    if "id" not in df.columns:
        df["id"] = range(1, len(df) + 1)

    for col in ["trainer", "commute", "manual"]:
        if col not in df.columns:
            df[col] = False
        df[col] = df[col].fillna(False).astype(bool)

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


def available_sports(df: pd.DataFrame) -> list[str]:
    if df.empty or "sport_label" not in df.columns:
        return []
    return sorted(df["sport_label"].dropna().astype(str).unique().tolist())


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

    mapping: dict[str, str] = {}
    for _, row in summary.iterrows():
        label = row["sport_label"]
        grouped = label
        if (label not in top_sports) or (row["pct"] < threshold_pct) or (row["activities"] < min_activities):
            grouped = "Altri"
        mapping[label] = grouped

    temp["sport_grouped"] = temp["sport_label"].map(mapping).fillna("Altri")
    return temp


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
    group_col = "sport_grouped" if "sport_grouped" in df.columns else "sport_label"
    out = (
        df.groupby(group_col, dropna=False)
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
    return out.rename(columns={group_col: "sport_grouped"})


def monthly_by_sport(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_col = "sport_grouped" if "sport_grouped" in df.columns else "sport_label"
    out = (
        df.groupby(["month_num", group_col], dropna=False)
        .agg(
            distance_km=("distance_km", "sum"),
            moving_time_h=("moving_time_h", "sum"),
            elevation_m=("elevation_m", "sum"),
            activities=("id", "count"),
        )
        .reset_index()
    )
    out["month"] = out["month_num"].map(MONTH_MAP)
    out = out.sort_values(["month_num", group_col])
    return out.rename(columns={group_col: "sport_grouped"})


def cumulative_by_year(df: pd.DataFrame, metric: str = "distance_km") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    temp = (
        df.groupby(["year", "month_num"], dropna=False)[metric]
        .sum()
        .reset_index()
        .sort_values(["year", "month_num"])
    )
    if temp.empty:
        return temp
    years = sorted(temp["year"].dropna().unique().tolist())
    parts = []
    for y in years:
        base = pd.DataFrame({"month_num": list(range(1, 13))})
        cur = temp[temp["year"] == y][["month_num", metric]]
        merged = base.merge(cur, on="month_num", how="left")
        merged[metric] = merged[metric].fillna(0)
        merged["year"] = y
        parts.append(merged)
    out = pd.concat(parts, ignore_index=True)
    out["cumulative"] = out.groupby("year")[metric].cumsum()
    out["month_label"] = out["month_num"].map(MONTH_MAP)
    return out


def trend_monthly(df: pd.DataFrame, metric: str = "distance_km") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = (
        df.groupby(["year", "month_num"], dropna=False)[metric]
        .sum()
        .reset_index()
    )
    if out.empty:
        return out
    parts = []
    for year in sorted(out["year"].dropna().unique().tolist()):
        base = pd.DataFrame({"month_num": list(range(1, 13))})
        cur = out[out["year"] == year][["month_num", metric]]
        merged = base.merge(cur, on="month_num", how="left")
        merged[metric] = merged[metric].fillna(0)
        merged["year"] = year
        parts.append(merged)
    out = pd.concat(parts, ignore_index=True)
    out["month"] = out["month_num"].map(MONTH_MAP)
    return out.sort_values(["year", "month_num"])


def compare_vs_previous_year(df: pd.DataFrame, metric: str = "distance_km") -> dict:
    if df.empty or df["year"].dropna().empty:
        return {"current": 0.0, "previous": 0.0, "delta_pct": 0.0, "current_year": date.today().year, "previous_year": date.today().year - 1}
    current_year = int(df["year"].max())
    previous_year = current_year - 1
    current_total = float(df.loc[df["year"] == current_year, metric].sum())
    prev_total = float(df.loc[df["year"] == previous_year, metric].sum())
    delta_pct = 0.0 if prev_total == 0 else ((current_total - prev_total) / prev_total) * 100.0
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
    rows = []
    top_dist = df.sort_values("distance_km", ascending=False).head(1)
    if not top_dist.empty:
        r = top_dist.iloc[0]
        rows.append({"label": "Distanza più lunga", "value": f"{r['distance_km']:.1f} km", "date": pd.to_datetime(r['start_date_local']).strftime('%d %b %Y'), "sport": r['sport_label']})
    top_run = df[df["sport_type"].isin(["Run", "TrailRun"])].sort_values("distance_km", ascending=False).head(1)
    if not top_run.empty:
        r = top_run.iloc[0]
        rows.append({"label": "Run più lunga", "value": f"{r['distance_km']:.1f} km", "date": pd.to_datetime(r['start_date_local']).strftime('%d %b %Y'), "sport": r['sport_label']})
    top_elev = df.sort_values("elevation_m", ascending=False).head(1)
    if not top_elev.empty:
        r = top_elev.iloc[0]
        rows.append({"label": "Dislivello più alto", "value": f"{r['elevation_m']:.0f} m", "date": pd.to_datetime(r['start_date_local']).strftime('%d %b %Y'), "sport": r['sport_label']})
    top_time = df.sort_values("moving_time_h", ascending=False).head(1)
    if not top_time.empty:
        r = top_time.iloc[0]
        rows.append({"label": "Tempo più lungo", "value": f"{r['moving_time_h']:.1f} h", "date": pd.to_datetime(r['start_date_local']).strftime('%d %b %Y'), "sport": r['sport_label']})
    return pd.DataFrame(rows)


def favorite_weekday(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"weekday": "-", "pct": 0.0}
    counts = df["weekday"].value_counts(dropna=True)
    if counts.empty:
        return {"weekday": "-", "pct": 0.0}
    wd = str(counts.index[0])
    pct = float(counts.iloc[0] / len(df) * 100.0)
    return {"weekday": wd, "pct": pct}


def most_active_week(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"week": "-", "activities": 0, "year": None}
    temp = (
        df.dropna(subset=["week"]).groupby(["year", "week"]).size().reset_index(name="activities").sort_values("activities", ascending=False)
    )
    if temp.empty:
        return {"week": "-", "activities": 0, "year": None}
    r = temp.iloc[0]
    return {"week": f"Settimana {int(r['week'])}", "activities": int(r['activities']), "year": int(r['year'])}


def primary_sport(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"sport": "-", "pct": 0.0}
    temp = df.groupby("sport_label")["distance_km"].sum().sort_values(ascending=False)
    if temp.empty:
        return {"sport": "-", "pct": 0.0}
    sport = str(temp.index[0])
    total = float(temp.sum())
    pct = float(temp.iloc[0] / total * 100.0) if total > 0 else 0.0
    return {"sport": sport, "pct": pct}


def distance_bucket_distribution(df: pd.DataFrame, mode: str = "count", bucket_col: str = "bucket") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    bins = [-0.001, 10, 25, 50, 100, float("inf")]
    labels = ["<10 km", "10-25 km", "25-50 km", "50-100 km", ">100 km"]
    temp = df.copy()
    temp[bucket_col] = pd.cut(temp["distance_km"], bins=bins, labels=labels)
    if mode == "count":
        return temp.groupby(bucket_col, observed=False).size().reset_index(name="count")
    return temp.groupby(bucket_col, observed=False)["distance_km"].sum().reset_index(name="count")


def personal_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = []
    for label, sort_col, fmt in [
        ("Distanza più lunga", "distance_km", lambda v: f"{v:.1f} km"),
        ("Tempo più lungo", "moving_time_h", lambda v: f"{v:.1f} h"),
        ("Dislivello più alto", "elevation_m", lambda v: f"{v:.0f} m"),
        ("Velocità media più alta", "avg_speed_kmh", lambda v: f"{v:.1f} km/h"),
    ]:
        top = df.sort_values(sort_col, ascending=False).head(1)
        if not top.empty:
            r = top.iloc[0]
            rows.append({"record": label, "value": fmt(r[sort_col]), "date": pd.to_datetime(r['start_date_local']).strftime('%d %b %Y')})
    return pd.DataFrame(rows)


def zone_proxy(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    temp = df.copy()
    score = temp["effort_score"].fillna(0)

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

    temp["zone"] = score.map(zone_name)
    out = (
        temp.groupby("zone", dropna=False)
        .agg(activities=("id", "count"), moving_time_h=("moving_time_h", "sum"))
        .reset_index()
    )
    order = ["Zona 1 (Recupero)", "Zona 2 (Endurance)", "Zona 3 (Tempo)", "Zona 4 (Soglia)", "Zona 5 (VO2 Max)"]
    out["zone"] = pd.Categorical(out["zone"], categories=order, ordered=True)
    out = out.sort_values("zone").reset_index(drop=True)
    total_a = out["activities"].sum()
    total_t = out["moving_time_h"].sum()
    out["activities_pct"] = np.where(total_a > 0, (out["activities"] / total_a) * 100.0, 0.0)
    out["time_pct"] = np.where(total_t > 0, (out["moving_time_h"] / total_t) * 100.0, 0.0)
    return out


def monthly_best_worst(df: pd.DataFrame, metric: str = "distance_km") -> dict:
    if df.empty:
        return {"best_month": "-", "best_value": 0.0, "worst_month": "-", "worst_value": 0.0}
    temp = df.groupby(["month_num", "month"], dropna=False)[metric].sum().reset_index().sort_values(metric, ascending=False)
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
    temp = df.dropna(subset=["year", "week"]).groupby(["year", "week"]).size().reset_index(name="activities")
    if temp.empty:
        return 0.0
    active_weeks = int((temp["activities"] > 0).sum())
    total_weeks = int(temp.shape[0])
    return round((active_weeks / total_weeks) * 100.0, 1) if total_weeks else 0.0
