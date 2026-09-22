"""Live status, viewers, category and followers from Twitch's Helix API.

Read-only stream data doesn't need the viewer's own login - an "app access
token" (client credentials grant) is enough, and that only needs a free
Client ID + Client Secret from https://dev.twitch.tv/console/apps. Nothing
is authorized on your behalf; this can only read what's already public.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
API_BASE = "https://api.twitch.tv/helix"
TIMEOUT = 6


@dataclass(frozen=True)
class TwitchStatus:
    is_live: bool = False
    title: str = ""
    category: str = ""
    viewer_count: int = 0
    follower_count: int | None = None

    def format(self) -> str:
        if not self.is_live:
            return ""
        parts = [f"\U0001f534 {self.category}" if self.category else "\U0001f534 LIVE"]
        parts.append(f"{self.viewer_count} viewers")
        if self.follower_count is not None:
            parts.append(f"{self.follower_count} followers")
        return " | ".join(parts)


class TwitchClient:
    def __init__(self, client_id: str, client_secret: str, username: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username.lstrip("@")
        self.last_error: str | None = None
        self._token: str | None = None
        self._token_expires = 0.0
        self._user_id: str | None = None
        self._cached = TwitchStatus()
        self._fetched_at = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.username)

    def current(self) -> TwitchStatus:
        if not self.configured:
            return TwitchStatus()

        now = time.monotonic()
        if now - self._fetched_at < 30:
            return self._cached

        self._fetched_at = now
        fetched = self._fetch()
        if fetched is not None:
            self._cached = fetched
        return self._cached

    def _headers(self) -> dict[str, str] | None:
        token = self._ensure_token()
        if token is None:
            return None
        return {"Client-Id": self.client_id, "Authorization": f"Bearer {token}"}

    def _ensure_token(self) -> str | None:
        if self._token and time.monotonic() < self._token_expires:
            return self._token

        body = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            }
        ).encode()
        request = urllib.request.Request(TOKEN_URL, data=body, method="POST")

        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self.last_error = f"token request failed: {exc}"
            return None

        token = payload.get("access_token")
        if not token:
            self.last_error = "no access token in response"
            return None

        self._token = token
        self._token_expires = time.monotonic() + payload.get("expires_in", 3600) - 60
        return token

    def _get(self, path: str, params: dict[str, str]) -> dict | None:
        headers = self._headers()
        if headers is None:
            return None
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request(f"{API_BASE}/{path}?{query}", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self.last_error = f"{path} failed: {exc}"
            return None

    def _resolve_user_id(self) -> str | None:
        if self._user_id:
            return self._user_id
        payload = self._get("users", {"login": self.username})
        if not payload or not payload.get("data"):
            return None
        self._user_id = payload["data"][0]["id"]
        return self._user_id

    def _fetch(self) -> TwitchStatus | None:
        user_id = self._resolve_user_id()
        if user_id is None:
            return None

        stream_payload = self._get("streams", {"user_id": user_id})
        if stream_payload is None:
            return None

        streams = stream_payload.get("data") or []
        if not streams:
            return TwitchStatus(is_live=False)

        stream = streams[0]

        followers = None
        followers_payload = self._get("channels/followers", {"broadcaster_id": user_id, "first": "1"})
        if followers_payload is not None:
            followers = followers_payload.get("total")

        return TwitchStatus(
            is_live=True,
            title=stream.get("title", ""),
            category=stream.get("game_name", ""),
            viewer_count=stream.get("viewer_count", 0),
            follower_count=followers,
        )
