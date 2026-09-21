"""Builds and pushes Discord Rich Presence from the current session state."""

from __future__ import annotations

import time
from typing import Any

from .state import SessionState

DEFAULT_APP_ID = "1234567890123456789"

VR_ICON = "vr"
DESKTOP_ICON = "desktop"
FALLBACK_IMAGE = "vrchat"


def build_presence(
    state: SessionState,
    *,
    show_players: bool = True,
    allow_join: bool = True,
) -> dict[str, Any]:
    """Assemble the pypresence payload for the current state.

    Discord accepts an https image URL directly as an asset key, so a world's
    own thumbnail can be shown without pre-uploading anything.
    """
    if not state.in_world:
        return {
            "details": "Not in a world",
            "large_image": FALLBACK_IMAGE,
            "large_text": "VRChat",
        }

    presence: dict[str, Any] = {
        "details": state.world_name or "Loading world...",
        "large_image": state.world_image_url or FALLBACK_IMAGE,
        "large_text": state.world_name or "VRChat",
    }

    if state.in_vr is not None:
        presence["small_image"] = VR_ICON if state.in_vr else DESKTOP_ICON
        presence["small_text"] = "VR" if state.in_vr else "Desktop"

    if show_players and state.player_count:
        presence["state"] = _describe_players(state)
        presence["party_size"] = [state.player_count, state.world_capacity or state.player_count]

    if state.joined_at is not None:
        presence["start"] = int(state.joined_at.timestamp())

    if allow_join and state.location:
        presence["join"] = state.location

    return presence


def _describe_players(state: SessionState) -> str:
    count = state.player_count
    if state.world_capacity:
        return f"{count} of {state.world_capacity} players"
    return f"{count} player" if count == 1 else f"{count} players"


def launch_url(location: str) -> str:
    """Deep link that opens VRChat straight into an instance."""
    world_id, _, instance_id = location.partition(":")
    return f"vrchat://launch?ref=vrcpresence&worldId={world_id}&instanceId={instance_id}"


class PresenceClient:
    """Thin wrapper over pypresence that tolerates Discord not running.

    Discord is frequently started after the game, so a client that connects
    once at startup and gives up leaves people with no presence at all. This
    retries quietly in the background instead.
    """

    def __init__(self, app_id: str = DEFAULT_APP_ID, *, retry_seconds: float = 30.0) -> None:
        self.app_id = app_id
        self.retry_seconds = retry_seconds
        self._rpc: Any = None
        self._last_attempt = 0.0
        self._last_payload: dict[str, Any] | None = None

    @property
    def connected(self) -> bool:
        return self._rpc is not None

    def connect(self) -> bool:
        if self._rpc is not None:
            return True

        now = time.monotonic()
        if now - self._last_attempt < self.retry_seconds:
            return False
        self._last_attempt = now

        try:
            from pypresence import Presence
        except ImportError:
            return False

        try:
            rpc = Presence(self.app_id)
            rpc.connect()
        except Exception:  # noqa: BLE001 - Discord being closed raises freely
            return False

        self._rpc = rpc
        return True

    def update(self, payload: dict[str, Any]) -> bool:
        """Push a presence payload, skipping no-op updates."""
        if payload == self._last_payload:
            return True
        if not self.connect():
            return False

        try:
            self._rpc.update(**payload)
        except Exception:  # noqa: BLE001 - drop the connection and retry later
            self._rpc = None
            return False

        self._last_payload = payload
        return True

    def clear(self) -> None:
        self._last_payload = None
        if self._rpc is None:
            return
        try:
            self._rpc.clear()
        except Exception:  # noqa: BLE001 - drop the connection and retry later
            self._rpc = None

    def close(self) -> None:
        self._last_payload = None
        rpc, self._rpc = self._rpc, None
        if rpc is None:
            return
        try:
            rpc.close()
        except Exception:  # noqa: BLE001 - shutdown path, nothing left to salvage
            return
