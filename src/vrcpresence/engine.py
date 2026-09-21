"""Wires the log watcher, VRChat API, Discord presence and chatbox together.

Deliberately GUI-free: the engine runs headless from the CLI just as well as
behind the Qt interface, and it is the only place session state is mutated.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from .config import Config, config_dir, data_dir
from .discord_presence import DEFAULT_APP_ID, PresenceClient, build_presence
from .events import Event, LeftRoom, PlayerJoin, PlayerLeave, WorldJoin, WorldName
from .history import History
from .log_watcher import LogWatcher
from .osc_client import ChatboxClient, format_chatbox_text
from .state import SessionState
from .vrchat_api import VRChatClient, WorldCache

Listener = Callable[[Event, SessionState], None]


@dataclass
class EngineStatus:
    log_found: bool = False
    discord_connected: bool = False
    vrchat_authenticated: bool = False


class Engine:
    def __init__(self, config: Config | None = None, *, log_watcher: LogWatcher | None = None) -> None:
        self.config = config or Config.load()
        self.state = SessionState()
        self.status = EngineStatus()

        self.watcher = log_watcher or LogWatcher()
        self.presence = PresenceClient(self.config.discord_app_id or DEFAULT_APP_ID)
        self.chatbox = ChatboxClient()
        self.vrchat = VRChatClient(
            cookie_path=config_dir() / "session.cookies",
            cache=WorldCache(data_dir() / "worlds.json"),
        )
        self.history = History(data_dir() / "history.db") if self.config.history_enabled else None

        self._listeners: list[Listener] = []
        self._chatbox_rotation = 0
        self._last_chatbox_push = 0.0

    def add_listener(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def start(self) -> None:
        if self.vrchat.restore_session():
            self.status.vrchat_authenticated = True

    def tick(self) -> list[Event]:
        """Advance one poll cycle. Safe to call on a timer."""
        events = self.watcher.poll()
        self.status.log_found = self.watcher.current_log is not None

        for event in events:
            self.state.apply(event)
            self._on_event(event)
            for listener in self._listeners:
                listener(event, self.state)

        if events:
            self._push_presence()

        self._maybe_push_chatbox()
        return events

    def _on_event(self, event: Event) -> None:
        if isinstance(event, WorldJoin):
            if self.history:
                self.history.start_visit(event.world_id, event.instance_id, None)
            self._enrich_world(event.world_id)

        elif isinstance(event, WorldName):
            if self.history:
                self.history.set_world_name(event.name)

        elif isinstance(event, PlayerJoin):
            if self.history:
                self.history.record_player(event.display_name)
                self.history.record_peak(self.state.player_count)
            self._notify_player(event.display_name, joined=True)

        elif isinstance(event, PlayerLeave):
            self._notify_player(event.display_name, joined=False)

        elif isinstance(event, LeftRoom):
            if self.history:
                self.history.end_visit()

    def _enrich_world(self, world_id: str) -> None:
        info = self.vrchat.get_world(world_id)
        if info is None:
            return
        if info.name:
            self.state.world_name = info.name
        self.state.world_image_url = info.image_url
        self.state.world_capacity = info.capacity

    def _notify_player(self, display_name: str, *, joined: bool) -> None:
        if not self.config.notifications_enabled:
            return
        from . import notifications

        verb = "joined" if joined else "left"
        notifications.notify(f"{display_name} {verb}", self.state.world_name or "VRChat")

    def _push_presence(self) -> None:
        if not self.config.discord_enabled:
            return
        if self.config.private_mode:
            self.presence.clear()
            self.status.discord_connected = self.presence.connected
            return

        payload = build_presence(
            self.state,
            show_players=self.config.show_players,
            allow_join=self.config.allow_join,
        )
        self.presence.update(payload)
        self.status.discord_connected = self.presence.connected

    def _maybe_push_chatbox(self) -> None:
        if not self.config.chatbox_enabled or not self.config.chatbox_templates:
            return
        now = time.monotonic()
        if now - self._last_chatbox_push < self.config.chatbox_interval:
            return
        self._last_chatbox_push = now

        template = self.config.chatbox_templates[
            self._chatbox_rotation % len(self.config.chatbox_templates)
        ]
        self._chatbox_rotation += 1
        self.chatbox.send(format_chatbox_text(template, self.chatbox_tokens()))

    def chatbox_tokens(self) -> dict[str, str]:
        mode = "" if self.state.in_vr is None else ("VR" if self.state.in_vr else "Desktop")
        return {
            "world": self.state.world_name or "Loading",
            "players": str(self.state.player_count),
            "capacity": str(self.state.world_capacity or ""),
            "mode": mode,
        }

    def run(self, *, stop: Callable[[], bool] | None = None) -> None:
        """Blocking headless loop."""
        self.start()
        try:
            while not (stop and stop()):
                self.tick()
                time.sleep(self.config.poll_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        if self.config.chatbox_enabled:
            self.chatbox.clear()
        self.presence.close()
        if self.history:
            self.history.end_visit()
            self.history.close()
