from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Property, QFileSystemWatcher, QObject, QTimer, Signal, Slot

from .. import __version__
from ..engine import Engine
from ..theming import SETTINGS_PATH, load_desktop_theme


class Bridge(QObject):
    """Exposes engine state to QML and pushes config changes back down."""

    changed = Signal()
    historyChanged = Signal()
    themeChanged = Signal()

    def __init__(self, engine: Engine) -> None:
        super().__init__()
        self._engine = engine
        self._engine.start()

        self._theme = load_desktop_theme()
        self._watch_theme()

        self._timer = QTimer(self)
        self._timer.setInterval(int(engine.config.poll_interval * 1000))
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _watch_theme(self) -> None:
        """Re-read the palette whenever the desktop rewrites it."""
        self._watcher = QFileSystemWatcher(self)
        if SETTINGS_PATH.is_file():
            self._watcher.addPath(str(SETTINGS_PATH))
        if SETTINGS_PATH.parent.is_dir():
            self._watcher.addPath(str(SETTINGS_PATH.parent))
        self._watcher.fileChanged.connect(self._reload_theme)
        self._watcher.directoryChanged.connect(self._reload_theme)

    def _reload_theme(self, *_args) -> None:
        # Editors replace rather than modify, which drops the watch.
        if SETTINGS_PATH.is_file() and str(SETTINGS_PATH) not in self._watcher.files():
            self._watcher.addPath(str(SETTINGS_PATH))

        theme = load_desktop_theme()
        if theme != self._theme:
            self._theme = theme
            self.themeChanged.emit()

    # --- desktop theme ----------------------------------------------------

    @Property(str, notify=themeChanged)
    def themeBase(self) -> str:
        return self._theme.color("base")

    @Property(str, notify=themeChanged)
    def themeMantle(self) -> str:
        return self._theme.color("mantle")

    @Property(str, notify=themeChanged)
    def themeSurface(self) -> str:
        return self._theme.color("surface0")

    @Property(str, notify=themeChanged)
    def themeSurfaceAlt(self) -> str:
        return self._theme.color("surface1")

    @Property(str, notify=themeChanged)
    def themeBorder(self) -> str:
        return self._theme.color("surface2")

    @Property(str, notify=themeChanged)
    def themeAccent(self) -> str:
        return self._theme.color("mauve")

    @Property(str, notify=themeChanged)
    def themeText(self) -> str:
        return self._theme.color("text")

    @Property(str, notify=themeChanged)
    def themeSubtext(self) -> str:
        return self._theme.color("subtext0")

    @Property(str, notify=themeChanged)
    def themeFaint(self) -> str:
        return self._theme.color("overlay1")

    @Property(str, notify=themeChanged)
    def themeGood(self) -> str:
        return self._theme.color("green")

    @Property(str, notify=themeChanged)
    def themeWarn(self) -> str:
        return self._theme.color("yellow")

    @Property(str, notify=themeChanged)
    def themeBad(self) -> str:
        return self._theme.color("red")

    @Property(str, notify=themeChanged)
    def themeFont(self) -> str:
        return self._theme.font_family

    @Property(int, notify=themeChanged)
    def themeRadius(self) -> int:
        return self._theme.radius

    @Property(str, notify=themeChanged)
    def themePreset(self) -> str:
        return self._theme.preset

    @Property(bool, notify=themeChanged)
    def followingDesktop(self) -> bool:
        return self._theme.following_desktop

    def _tick(self) -> None:
        events = self._engine.tick()
        self.changed.emit()
        if events:
            self.historyChanged.emit()

    # --- session state -------------------------------------------------

    @Property(bool, notify=changed)
    def inWorld(self) -> bool:
        return self._engine.state.in_world

    @Property(bool, notify=changed)
    def vrchatRunning(self) -> bool:
        return self._engine.status.vrchat_running

    @Property(str, notify=changed)
    def headline(self) -> str:
        if not self._engine.status.vrchat_running:
            return "VRChat is not running"
        if not self._engine.state.in_world:
            return "Between worlds"
        return self._engine.state.world_name or "Loading world..."

    @Property(str, notify=changed)
    def subheadline(self) -> str:
        if not self._engine.status.vrchat_running:
            return "Start VRChat and this fills in automatically"
        if not self._engine.state.in_world:
            return "Waiting for an instance"
        return ""

    @Property(str, notify=changed)
    def instanceType(self) -> str:
        """public / friends+ / private, pulled out of the instance id."""
        instance = self._engine.state.instance_id or ""
        for marker, label in (
            ("~private", "private"),
            ("~friends", "friends"),
            ("~hidden", "friends+"),
            ("~group", "group"),
        ):
            if marker in instance:
                return label
        return "public" if instance else ""

    @Property(str, notify=changed)
    def sessionTime(self) -> str:
        joined = self._engine.state.joined_at
        if joined is None:
            return ""
        minutes = int((datetime.now(timezone.utc) - joined).total_seconds() // 60)
        if minutes < 60:
            return f"{minutes}m"
        return f"{minutes // 60}h {minutes % 60}m"

    @Property(str, notify=historyChanged)
    def todaySummary(self) -> str:
        history = self._engine.history
        if history is None:
            return "history off"
        today = datetime.now().astimezone().date()
        minutes = 0.0
        worlds = 0
        for visit in history.recent_visits(limit=500):
            if visit.joined_at.astimezone().date() != today:
                continue
            worlds += 1
            minutes += (visit.duration_seconds or 0) / 60
        if not worlds:
            return "nothing yet"
        return f"{worlds}w / {minutes / 60:.1f}h"

    @Property(str, notify=changed)
    def worldName(self) -> str:
        return self._engine.state.world_name or ""

    @Property(str, notify=changed)
    def worldImageUrl(self) -> str:
        return self._engine.state.world_image_url or ""

    @Property(int, notify=changed)
    def playerCount(self) -> int:
        return self._engine.state.player_count

    @Property(int, notify=changed)
    def worldCapacity(self) -> int:
        return self._engine.state.world_capacity or 0

    @Property(str, notify=changed)
    def mode(self) -> str:
        if self._engine.state.in_vr is None:
            return ""
        return "VR" if self._engine.state.in_vr else "Desktop"

    @Property("QVariantList", notify=changed)
    def players(self) -> list:
        return list(self._engine.state.players)

    # --- status ---------------------------------------------------------

    @Property(bool, notify=changed)
    def logFound(self) -> bool:
        return self._engine.status.log_found

    @Property(str, notify=changed)
    def logPath(self) -> str:
        log = self._engine.watcher.current_log
        return str(log) if log else ""

    @Property(bool, notify=changed)
    def discordConnected(self) -> bool:
        return self._engine.status.discord_connected

    @Property(bool, notify=changed)
    def vrchatAuthenticated(self) -> bool:
        return self._engine.status.vrchat_authenticated

    @Property(str, constant=True)
    def version(self) -> str:
        return __version__

    # --- settings -------------------------------------------------------

    @Property(bool, notify=changed)
    def discordEnabled(self) -> bool:
        return self._engine.config.discord_enabled

    @Property(str, notify=changed)
    def discordAppId(self) -> str:
        return self._engine.config.discord_app_id

    @Property(str, notify=changed)
    def discordStatus(self) -> str:
        """What the status pill should say: setup state, not just on/off."""
        if not self._engine.config.discord_enabled:
            return "discord off"
        if not self._engine.config.discord_app_id:
            return "needs app id"
        if self._engine.config.private_mode:
            return "private"
        return "discord" if self._engine.status.discord_connected else "connecting"

    @Property(bool, notify=changed)
    def discordReady(self) -> bool:
        return self._engine.status.discord_connected

    @Slot(str)
    def setDiscordAppId(self, value: str) -> None:
        value = value.strip()
        self._engine.config.discord_app_id = value
        self._engine.config.save()
        self._engine.reload_presence_client()
        self.changed.emit()

    @Property(bool, notify=changed)
    def showPlayers(self) -> bool:
        return self._engine.config.show_players

    @Property(bool, notify=changed)
    def allowJoin(self) -> bool:
        return self._engine.config.allow_join

    @Property(bool, notify=changed)
    def privateMode(self) -> bool:
        return self._engine.config.private_mode

    @Property(bool, notify=changed)
    def chatboxEnabled(self) -> bool:
        return self._engine.config.chatbox_enabled

    @Property(bool, notify=changed)
    def notificationsEnabled(self) -> bool:
        return self._engine.config.notifications_enabled

    @Property(bool, notify=changed)
    def historyEnabled(self) -> bool:
        return self._engine.config.history_enabled

    def _set(self, field: str, value: bool) -> None:
        setattr(self._engine.config, field, value)
        self._engine.config.save()
        self.changed.emit()

    @Slot(bool)
    def setDiscordEnabled(self, value: bool) -> None:
        self._set("discord_enabled", value)
        if not value:
            self._engine.presence.clear()

    @Property(bool, notify=changed)
    def hidePrivate(self) -> bool:
        return self._engine.config.hide_private_instances

    @Property(bool, notify=changed)
    def chatboxMedia(self) -> bool:
        return self._engine.config.chatbox_media

    @Property(int, notify=changed)
    def chatboxInterval(self) -> int:
        return self._engine.config.chatbox_interval

    @Property(bool, notify=changed)
    def sessionHistoryOnly(self) -> bool:
        return self._engine.config.session_history_only

    @Property(str, notify=changed)
    def chatboxPreview(self) -> str:
        """Exactly what would be sent to the chatbox right now."""
        from ..osc_client import format_chatbox_text

        templates = self._engine.config.chatbox_templates
        if not templates:
            return ""
        return format_chatbox_text(templates[0], self._engine.chatbox_tokens())

    @Property(str, notify=changed)
    def nowPlaying(self) -> str:
        return self._engine.track.format() or "nothing playing"

    @Property(bool, notify=changed)
    def chatboxTyping(self) -> bool:
        return self._engine.config.chatbox_typing

    @Slot(bool)
    def setChatboxMedia(self, value: bool) -> None:
        self._set("chatbox_media", value)

    @Slot(bool)
    def setChatboxTyping(self, value: bool) -> None:
        self._set("chatbox_typing", value)
        if not value:
            self._engine.chatbox.set_typing(False)

    @Slot(int)
    def nudgeChatboxInterval(self, delta: int) -> None:
        current = self._engine.config.chatbox_interval
        self._set("chatbox_interval", max(3, min(60, current + delta)))

    @Slot()
    def sendChatboxNow(self) -> None:
        from ..osc_client import format_chatbox_text

        templates = self._engine.config.chatbox_templates
        if not templates:
            return
        text = format_chatbox_text(templates[0], self._engine.chatbox_tokens())
        self._engine.chatbox.send(text, notify=True)

    @Slot(bool)
    def setSessionHistoryOnly(self, value: bool) -> None:
        self._set("session_history_only", value)

    @Property(str, notify=changed)
    def chatboxTemplate(self) -> str:
        templates = self._engine.config.chatbox_templates
        return templates[0] if templates else ""

    @Slot(bool)
    def setHidePrivate(self, value: bool) -> None:
        self._set("hide_private_instances", value)

    @Slot(str)
    def setChatboxTemplate(self, value: str) -> None:
        self._engine.config.chatbox_templates = [value] if value.strip() else []
        self._engine.config.save()
        self.changed.emit()

    @Slot(bool)
    def setShowPlayers(self, value: bool) -> None:
        self._set("show_players", value)

    @Slot(bool)
    def setAllowJoin(self, value: bool) -> None:
        self._set("allow_join", value)

    @Slot(bool)
    def setPrivateMode(self, value: bool) -> None:
        self._set("private_mode", value)
        if value:
            self._engine.presence.clear()

    @Slot(bool)
    def setChatboxEnabled(self, value: bool) -> None:
        self._set("chatbox_enabled", value)
        if not value:
            self._engine.chatbox.clear()

    @Slot(bool)
    def setNotificationsEnabled(self, value: bool) -> None:
        self._set("notifications_enabled", value)

    @Slot(bool)
    def setHistoryEnabled(self, value: bool) -> None:
        self._set("history_enabled", value)

    # --- history ---------------------------------------------------------

    @Property("QVariantList", notify=historyChanged)
    def visits(self) -> list:
        history = self._engine.history
        if history is None:
            return []
        rows = []
        for visit in history.recent_visits(limit=100):
            duration = visit.duration_seconds
            rows.append(
                {
                    "when": visit.joined_at.astimezone().strftime("%H:%M"),
                    "name": visit.world_name or visit.world_id,
                    # 0 is a real duration, not a missing one.
                    "duration": "now" if duration is None else f"{max(1, duration / 60):.0f}m",
                    "peak": visit.peak_players,
                }
            )
        return rows

    @Property("QVariantList", notify=historyChanged)
    def peopleMet(self) -> list:
        history = self._engine.history
        if history is None:
            return []
        return [
            {"name": name, "shared": f"{count}x"} for name, count in history.people_met(limit=100)
        ]

    @Slot()
    def clearHistory(self) -> None:
        if self._engine.history is None:
            return
        self._engine.history.clear()
        self.historyChanged.emit()
        self.changed.emit()

    @Property("QVariantList", notify=historyChanged)
    def historyTotals(self) -> list:
        history = self._engine.history
        totals = history.totals() if history else {"visits": 0, "unique_worlds": 0, "seconds": 0.0, "people_met": 0}
        return [
            {"label": "visits", "value": str(totals["visits"])},
            {"label": "worlds", "value": str(totals["unique_worlds"])},
            {"label": "hours", "value": f"{totals['seconds'] / 3600:.1f}"},
            {"label": "people met", "value": str(totals["people_met"])},
        ]

    def shutdown(self) -> None:
        self._timer.stop()
        self._engine.shutdown()
