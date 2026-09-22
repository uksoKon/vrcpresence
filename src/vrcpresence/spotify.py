"""Spotify integration: liked/explicit/shuffle/repeat/device/volume/queue.

Uses the Authorization Code + PKCE flow, which needs only a free Client ID
from https://developer.spotify.com/dashboard (no secret to protect, which
matters for a desktop app) with a redirect URI of
http://127.0.0.1:8888/callback added in the app's settings.

The one-time login opens a browser and catches the redirect with a small
local HTTP server; after that, tokens refresh themselves and are cached on
disk like the VRChat API session.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import ClassVar

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"
REDIRECT_PORT = 8888
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/callback"
SCOPES = "user-read-playback-state user-read-currently-playing user-library-read"
TIMEOUT = 6


@dataclass(frozen=True)
class SpotifyTrack:
    title: str = ""
    artist: str = ""
    is_playing: bool = False
    is_liked: bool | None = None
    shuffle: bool = False
    repeat: str = "off"
    device: str = ""
    volume: int | None = None
    explicit: bool = False
    queue_next: str = ""
    progress_seconds: float = 0.0

    @property
    def is_empty(self) -> bool:
        return not self.title


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


class _CallbackHandler(BaseHTTPRequestHandler):
    result: ClassVar[dict[str, str]] = {}

    def do_GET(self) -> None:
        query = urllib.parse.urlparse(self.path).query
        params = dict(urllib.parse.parse_qsl(query))
        _CallbackHandler.result = params

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        message = "Signed in - you can close this tab." if "code" in params else "Sign-in failed."
        self.wfile.write(f"<html><body><p>{message}</p></body></html>".encode())

    def log_message(self, *args) -> None:  # silence default request logging
        return


class SpotifyClient:
    def __init__(self, client_id: str, token_path: Path) -> None:
        self.client_id = client_id
        self.token_path = Path(token_path)
        self.last_error: str | None = None
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at = 0.0
        self._load()

    @property
    def authenticated(self) -> bool:
        return bool(self._refresh_token)

    def _load(self) -> None:
        if not self.token_path.is_file():
            return
        try:
            data = json.loads(self.token_path.read_text())
        except (OSError, json.JSONDecodeError):
            return
        self._refresh_token = data.get("refresh_token")

    def _save(self) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps({"refresh_token": self._refresh_token}))
        self.token_path.chmod(0o600)

    def login(self, *, timeout: float = 120) -> bool:
        """Opens a browser for the one-time authorization; blocks until done."""
        self.last_error = None
        verifier, challenge = _pkce_pair()

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
        webbrowser.open(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

        _CallbackHandler.result = {}
        server = HTTPServer(("127.0.0.1", REDIRECT_PORT), _CallbackHandler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        server.server_close()

        code = _CallbackHandler.result.get("code")
        if not code:
            self.last_error = _CallbackHandler.result.get("error", "sign-in timed out")
            return False

        return self._exchange_code(code, verifier)

    def _exchange_code(self, code: str, verifier: str) -> bool:
        body = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": self.client_id,
                "code_verifier": verifier,
            }
        ).encode()
        return self._request_token(body)

    def _refresh(self) -> bool:
        if not self._refresh_token:
            return False
        body = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self.client_id,
            }
        ).encode()
        return self._request_token(body)

    def _request_token(self, body: bytes) -> bool:
        request = urllib.request.Request(TOKEN_URL, data=body, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self.last_error = f"token exchange failed: {exc}"
            return False

        if "access_token" not in payload:
            self.last_error = payload.get("error_description", "no access token returned")
            return False

        self._access_token = payload["access_token"]
        self._expires_at = time.monotonic() + payload.get("expires_in", 3600) - 60
        if payload.get("refresh_token"):
            self._refresh_token = payload["refresh_token"]
            self._save()
        return True

    def _ensure_token(self) -> str | None:
        if self._access_token and time.monotonic() < self._expires_at:
            return self._access_token
        if self._refresh():
            return self._access_token
        return None

    def now_playing(self) -> SpotifyTrack:
        token = self._ensure_token()
        if token is None:
            return SpotifyTrack()

        request = urllib.request.Request(
            f"{API_BASE}/me/player", headers={"Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                if response.status == 204:
                    return SpotifyTrack()
                payload = json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self.last_error = f"now-playing request failed: {exc}"
            return SpotifyTrack()

        item = payload.get("item") or {}
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        device = payload.get("device") or {}

        return SpotifyTrack(
            title=item.get("name", ""),
            artist=artists,
            is_playing=bool(payload.get("is_playing")),
            shuffle=bool(payload.get("shuffle_state")),
            repeat=payload.get("repeat_state", "off"),
            device=device.get("name", ""),
            volume=device.get("volume_percent"),
            explicit=bool(item.get("explicit")),
            progress_seconds=payload.get("progress_ms", 0) / 1000,
        )


def format_track(track: SpotifyTrack, template: str = "{title} - {artist}") -> str:
    if track.is_empty:
        return ""
    text = template.replace("{title}", track.title).replace("{artist}", track.artist)
    if track.explicit:
        text = f"\U0001f51e {text}"
    return text
