from __future__ import annotations

from typing import Any
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

        return all_items
