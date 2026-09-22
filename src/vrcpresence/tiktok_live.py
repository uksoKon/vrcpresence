"""Follower count and live events from TikTok, via the TikTokLive package.

Needs only a public TikTok username - no login, no API key. TikTokLive
connects to TikTok's public webcast feed the same way a browser watching the
live page does. It only produces events while that account is actually live.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


def available() -> bool:
    try:
        import TikTokLive  # noqa: F401
    except ImportError:
        return False
    return True


@dataclass
class TikTokState:
    is_live: bool = False
    viewer_count: int = 0
    follower_count: int | None = None
    recent_events: list[str] = field(default_factory=list)
    updated_at: float = 0.0


class TikTokLiveClient:
    """Runs TikTokLive's own event loop on a background thread."""

    def __init__(self, username: str) -> None:
        self.username = username.lstrip("@")
        self.state = TikTokState()
        self.connected = False
        self.last_error: str | None = None
        self._thread: threading.Thread | None = None
        self._client = None

    def start(self) -> None:
        if self._thread is not None or not self.username:
            return
        if not available():
            self.last_error = "TikTokLive package is not installed"
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        # disconnect() is a coroutine and client.run() owns the event loop on
        # the background thread, so it has to be scheduled onto that loop
        # rather than awaited directly. There is no public accessor for the
        # loop in this version of TikTokLive, only the private _asyncio_loop
        # attribute - if that name changes, this degrades to "thread keeps
        # running until process exit" rather than raising, since it's daemon.
        if self._client is not None:
            try:
                import asyncio

                loop = getattr(self._client, "_asyncio_loop", None)
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self._client.disconnect(), loop)
            except Exception:  # noqa: BLE001 - shutdown path, never allowed to raise
                self.last_error = "TikTok client did not shut down cleanly"
        self._thread = None
        self.connected = False

    def _run(self) -> None:
        try:
            from TikTokLive import TikTokLiveClient as _Client
            from TikTokLive.events import (
                ConnectEvent,
                DisconnectEvent,
                FollowEvent,
                GiftEvent,
                LiveEndEvent,
                RoomUserSeqEvent,
            )
        except ImportError as exc:
            self.last_error = str(exc)
            return

        client = _Client(unique_id=f"@{self.username}")
        self._client = client

        @client.on(ConnectEvent)
        async def on_connect(_event):
            self.connected = True
            self.state.is_live = True
            self.state.updated_at = time.monotonic()

        @client.on(DisconnectEvent)
        @client.on(LiveEndEvent)
        async def on_end(_event):
            self.connected = False
            self.state.is_live = False

        @client.on(RoomUserSeqEvent)
        async def on_viewers(event):
            # `total` is the live viewer count shown on-screen; `total_user`
            # is cumulative unique viewers, which isn't what we want here.
            self.state.viewer_count = getattr(event, "total", 0)
            self.state.updated_at = time.monotonic()

        @client.on(FollowEvent)
        async def on_follow(event):
            name = getattr(getattr(event, "user", None), "nickname", "someone")
            self._push_event(f"{name} followed")

        @client.on(GiftEvent)
        async def on_gift(event):
            name = getattr(getattr(event, "user", None), "nickname", "someone")
            gift = getattr(getattr(event, "gift", None), "name", "a gift")
            self._push_event(f"{name} sent {gift}")

        try:
            client.run()
        except Exception as exc:  # noqa: BLE001 - background thread, surfaced as text
            self.last_error = str(exc)
            self.connected = False

    def _push_event(self, text: str) -> None:
        self.state.recent_events.append(text)
        self.state.recent_events[:] = self.state.recent_events[-5:]
        self.state.updated_at = time.monotonic()


def format_status(state: TikTokState) -> str:
    if not state.is_live:
        return ""
    parts = ["\U0001f534 LIVE", f"{state.viewer_count} watching"]
    if state.recent_events:
        parts.append(state.recent_events[-1])
    return " | ".join(parts)
