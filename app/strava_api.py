from __future__ import annotations

from typing import Any
import statistics

import requests

from app.config import Settings


AUTH_URL = "https://www.strava.com/oauth/token"
BASE_URL = "https://www.strava.com/api/v3"


class StravaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.access_token: str | None = None

    def refresh_access_token(self) -> str:
        response = requests.post(
            AUTH_URL,
            data={
                "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.settings.refresh_token,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        return self.access_token

    def _headers(self) -> dict[str, str]:
        if not self.access_token:
            self.refresh_access_token()
        return {"Authorization": f"Bearer {self.access_token}"}

    def list_activities(self, after_ts: int, before_ts: int | None = None) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        page = 1

        while True:
            params: dict[str, Any] = {
                "after": after_ts,
                "page": page,
                "per_page": self.settings.activities_per_page,
            }
            if before_ts is not None:
                params["before"] = before_ts

            response = requests.get(
                f"{BASE_URL}/athlete/activities",
                headers=self._headers(),
                params=params,
                timeout=60,
            )
            response.raise_for_status()
            items = response.json()

            if not items:
                break

            all_items.extend(items)
            if len(items) < self.settings.activities_per_page:
                break
            page += 1

        if getattr(self.settings, "enrich_hr_streams", True):
            return self.enrich_activities_with_hr_zones(all_items)
        return all_items

    def get_activity_streams(self, activity_id: int | str, keys: list[str] | None = None) -> dict[str, Any]:
        """Return Strava streams keyed by type for a single activity.

        Strava returns an empty payload or omits heartrate when the activity has
        no HR data or the token scope does not allow activity streams. In those
        cases we return an empty dict and the caller falls back gracefully.
        """
        requested_keys = keys or ["time", "heartrate"]
        response = requests.get(
            f"{BASE_URL}/activities/{activity_id}/streams",
            headers=self._headers(),
            params={"keys": ",".join(requested_keys), "key_by_type": "true"},
            timeout=60,
        )
        if response.status_code in {403, 404}:
            return {}
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def enrich_activities_with_hr_zones(self, activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add real HR-zone seconds to activities using HR streams.

        Zones use the user-provided HRmax stored in Settings.hr_max_bpm.
        Boundaries are classic HRmax percentages:
        Z1 < 60%, Z2 60-70%, Z3 70-80%, Z4 80-90%, Z5 >= 90%.
        """
        enriched: list[dict[str, Any]] = []
        for activity in activities:
            item = dict(activity)
            activity_id = item.get("id")
            has_hr = bool(item.get("has_heartrate") or item.get("average_heartrate") or item.get("max_heartrate"))
            if activity_id and has_hr:
                try:
                    streams = self.get_activity_streams(activity_id, keys=["time", "heartrate"])
                    item.update(_hr_zone_seconds_from_streams(streams, hr_max_bpm=getattr(self.settings, "hr_max_bpm", 198)))
                except requests.HTTPError:
                    item.update(_empty_hr_zone_payload())
                except Exception:
                    item.update(_empty_hr_zone_payload())
            else:
                item.update(_empty_hr_zone_payload())
            enriched.append(item)
        return enriched


def _empty_hr_zone_payload() -> dict[str, Any]:
    return {
        "hr_zone_1_s": 0.0,
        "hr_zone_2_s": 0.0,
        "hr_zone_3_s": 0.0,
        "hr_zone_4_s": 0.0,
        "hr_zone_5_s": 0.0,
        "hr_zone_total_s": 0.0,
        "has_hr_stream": False,
        "hr_stream_samples": 0,
    }


def _stream_data(streams: dict[str, Any], key: str) -> list[Any]:
    stream = streams.get(key, {}) if isinstance(streams, dict) else {}
    if isinstance(stream, dict):
        data = stream.get("data", [])
        return data if isinstance(data, list) else []
    return []


def _sample_durations_seconds(time_values: list[Any], sample_count: int) -> list[float]:
    if sample_count <= 0:
        return []
    if len(time_values) >= 2:
        times = []
        for value in time_values[:sample_count]:
            try:
                times.append(float(value))
            except (TypeError, ValueError):
                times.append(float("nan"))
        durations: list[float] = []
        valid_deltas: list[float] = []
        for idx in range(sample_count - 1):
            if not (times[idx] == times[idx] and times[idx + 1] == times[idx + 1]):
                durations.append(1.0)
                continue
            delta = max(0.0, times[idx + 1] - times[idx])
            if delta > 0:
                valid_deltas.append(delta)
            durations.append(delta if delta > 0 else 1.0)
        last_delta = statistics.median(valid_deltas) if valid_deltas else 1.0
        durations.append(max(1.0, min(float(last_delta), 10.0)))
        return durations
    return [1.0] * sample_count


def _hr_zone_seconds_from_streams(streams: dict[str, Any], hr_max_bpm: int) -> dict[str, Any]:
    heartrates = _stream_data(streams, "heartrate")
    if not heartrates:
        return _empty_hr_zone_payload()

    time_values = _stream_data(streams, "time")
    sample_count = len(heartrates)
    durations = _sample_durations_seconds(time_values, sample_count)

    z1_upper = hr_max_bpm * 0.60
    z2_upper = hr_max_bpm * 0.70
    z3_upper = hr_max_bpm * 0.80
    z4_upper = hr_max_bpm * 0.90

    zone_seconds = {idx: 0.0 for idx in range(1, 6)}
    for raw_hr, seconds in zip(heartrates, durations):
        try:
            hr = float(raw_hr)
        except (TypeError, ValueError):
            continue
        if hr <= 0:
            continue
        if hr < z1_upper:
            zone = 1
        elif hr < z2_upper:
            zone = 2
        elif hr < z3_upper:
            zone = 3
        elif hr < z4_upper:
            zone = 4
        else:
            zone = 5
        zone_seconds[zone] += float(seconds)

    total = sum(zone_seconds.values())
    return {
        "hr_zone_1_s": zone_seconds[1],
        "hr_zone_2_s": zone_seconds[2],
        "hr_zone_3_s": zone_seconds[3],
        "hr_zone_4_s": zone_seconds[4],
        "hr_zone_5_s": zone_seconds[5],
        "hr_zone_total_s": total,
        "has_hr_stream": total > 0,
        "hr_stream_samples": sample_count,
    }
