"""Wires the log watcher, VRChat API, Discord presence and chatbox together.

Deliberately GUI-free: the engine runs headless from the CLI just as well as
behind the Qt interface, and it is the only place session state is mutated.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from .builder import build_line
from .components import ComponentSources, collect
from .config import Config, config_dir, data_dir
from .discord_presence import PresenceClient, build_presence
from .events import Event, LeftRoom, PlayerJoin, PlayerLeave, WorldJoin, WorldName
from .history import History
from .intellichat import IntelliChatConfig, IntelliChatService
from .log_watcher import LogWatcher
from .media import NowPlaying, now_playing
from .osc_client import MAX_CHATBOX_CHARS, ChatboxClient, format_chatbox_text
from .process import vrchat_running
from .state import SessionState
from .vrchat_api import VRChatClient, WorldCache

Listener = Callable[[Event, SessionState], None]


@dataclass
class EngineStatus:
    log_found: bool = False
    discord_connected: bool = False
    vrchat_authenticated: bool = False
    vrchat_running: bool = False


class Engine:
    def __init__(
        self,
        config: Config | None = None,
        *,
        log_watcher: LogWatcher | None = None,
        is_running: Callable[[], bool] = vrchat_running,
    ) -> None:
        self.config = config or Config.load()
        self._is_running = is_running
        self.state = SessionState()
        self.status = EngineStatus()

        self.watcher = log_watcher or LogWatcher()
        self.presence = PresenceClient(self.config.discord_app_id)
        self.chatbox = ChatboxClient(self.config.osc_host, self.config.osc_port)
        self.vrchat = VRChatClient(
            cookie_path=config_dir() / "session.cookies",
            cache=WorldCache(data_dir() / "worlds.json"),
        )
        self.history = History(data_dir() / "history.db") if self.config.history_enabled else None

        self._listeners: list[Listener] = []
        self._chatbox_rotation = 0
        self._last_chatbox_push = 0.0
        # Polled on the tick, never from a UI binding: querying playerctl is a
        # subprocess call, and doing that inside a QML binding blocks the GUI
        # thread every time the interface refreshes.
        self.track = NowPlaying()
        self._last_media_poll = 0.0
        self.sources = ComponentSources.create(self.config)
        self.last_line = ""
        self.intellichat = IntelliChatService()
        self._last_spoken = ""

    def add_listener(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def start(self) -> None:
        if self.vrchat.restore_session():
            self.status.vrchat_authenticated = True

    def tick(self) -> list[Event]:
        """Advance one poll cycle. Safe to call on a timer."""
        was_running = self.status.vrchat_running
        self.status.vrchat_running = self._is_running()

        if not self.status.vrchat_running:
            # The last log file still describes the last world visited, so
            # without this the UI reports a session that ended hours ago.
            if was_running or self.state.in_world:
                self._end_session()
            self.watcher.poll()
            self.status.log_found = self.watcher.current_log is not None
            return []

        events = self.watcher.poll()
        self.status.log_found = self.watcher.current_log is not None

        for event in events:
            self.state.apply(event)
            self._on_event(event)
            for listener in self._listeners:
                listener(event, self.state)

        if events:
            self._push_presence()

        self._refresh_media()
        self._maybe_push_chatbox()
        return events

    def _refresh_media(self) -> None:
        if not self.config.chatbox_media:
            self.track = NowPlaying()
            return
        now = time.monotonic()
        if now - self._last_media_poll < 3.0:
            return
        self._last_media_poll = now
        self.track = now_playing()

    def _end_session(self) -> None:
        """VRChat closed: drop the stale world and stop broadcasting it."""
        self.state.apply(LeftRoom())
        self.state.in_vr = None
        self.state.local_user = None
        if self.history:
            self.history.end_visit()
            if self.config.session_history_only:
                # History is for the session you're in, not a permanent log.
                self.history.clear()
        if self.config.discord_enabled:
            self.presence.clear()
        if self.config.chatbox_enabled:
            self.chatbox.clear()

    def reload_presence_client(self) -> None:
        """Rebuild the Discord client after the application ID changes."""
        self.presence.close()
        self.presence = PresenceClient(self.config.discord_app_id)
        self.status.discord_connected = False

    def reload_osc_client(self) -> None:
        """Rebuild the chatbox sender after the OSC host/port changes.

        This is the "Standalone" setup: point it at a Quest's IP on your
        network instead of 127.0.0.1 to run this on a separate PC.
        """
        self.chatbox = ChatboxClient(self.config.osc_host, self.config.osc_port)

    def spotify_login(self) -> bool:
        """Opens a browser for the one-time Spotify sign-in. Blocks briefly."""
        if not self.sources.spotify:
            return False
        return self.sources.spotify.login()

    def _on_event(self, event: Event) -> None:
        if isinstance(event, WorldJoin):
            if self.history:
                self.history.start_visit(event.world_id, event.instance_id, None)
            self._enrich_world(event.world_id)

        elif isinstance(event, WorldName):
            if self.history:
                self.history.set_world_name(event.name)

        elif isinstance(event, PlayerJoin):
            is_self = event.display_name == self.state.local_user
            if self.history:
                if not is_self:
                    self.history.record_player(event.display_name)
                self.history.record_peak(self.state.player_count)
            if not is_self:
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

        instance = self.state.instance_id or ""
        is_private = any(m in instance for m in ("~private", "~friends", "~hidden", "~group"))
        if self.config.hide_private_instances and is_private:
            self.presence.clear()
            self.status.discord_connected = self.presence.connected
            return

        payload = build_presence(
            self.state,
            show_players=self.config.show_players,
            # A join link into a private instance would not work anyway.
            allow_join=self.config.allow_join and not is_private,
        )
        self.presence.update(payload)
        self.status.discord_connected = self.presence.connected

    def _maybe_push_chatbox(self) -> None:
        if not self.config.chatbox_enabled:
            return
        if not self.config.chatbox_components and not self.config.chatbox_templates:
            return
        now = time.monotonic()
        if now - self._last_chatbox_push < self.config.chatbox_interval:
            return
        self._last_chatbox_push = now

        text = self.compose_line()
        self.chatbox.send(text)

        if self.config.tts_enabled and self.config.tts_speak_chatbox and text != self._last_spoken:
            from . import tts

            tts.speak(text, voice=self.config.tts_piper_voice or None)
            self._last_spoken = text

    def compose_line(self) -> str:
        """The exact text that goes to VRChat, however it is assembled."""
        if self.config.chatbox_components:
            components = collect(
                self.config,
                self.state,
                self.sources,
                running=self.status.vrchat_running,
                track=self.track,
            )
            text = build_line(components, in_vr=self.state.in_vr).text
        else:
            templates = self.config.chatbox_templates
            if not templates:
                self.last_line = ""
                return ""
            template = templates[self._chatbox_rotation % len(templates)]
            self._chatbox_rotation += 1
            text = format_chatbox_text(template, self.chatbox_tokens())

        if self.config.intellichat_enabled:
            ai_config = IntelliChatConfig(
                enabled=self.config.intellichat_enabled,
                api_key=self.config.intellichat_api_key,
                api_base=self.config.intellichat_api_base,
                model=self.config.intellichat_model,
            )
            text = self.intellichat.process(text, ai_config, limit=MAX_CHATBOX_CHARS)

        self.last_line = text
        return text

    def chatbox_tokens(self) -> dict[str, str]:
        mode = "" if self.state.in_vr is None else ("VR" if self.state.in_vr else "Desktop")
        track = self.track if self.config.chatbox_media else NowPlaying()
        if not self.status.vrchat_running:
            world = "VRChat offline"
        elif not self.state.in_world:
            world = "Between worlds"
        else:
            world = self.state.world_name or "Loading"
        return {
            "world": world,
            "players": str(self.state.player_count),
            "capacity": str(self.state.world_capacity or ""),
            "mode": mode,
            "time": datetime.now().astimezone().strftime("%H:%M"),
            "song": track.format(),
            "title": track.title,
            "artist": track.artist,
            "player": track.player,
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
        self.sources.shutdown()
        if self.history:
            self.history.end_visit()
            self.history.close()
