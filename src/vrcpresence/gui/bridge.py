from __future__ import annotations

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from .. import __version__
from ..config import data_dir
from ..engine import Engine
from ..history import History


class Bridge(QObject):
    """Exposes engine state to QML and pushes config changes back down."""

    changed = Signal()
    historyChanged = Signal()

    def __init__(self, engine: Engine) -> None:
        super().__init__()
        self._engine = engine
        self._engine.start()

        self._timer = QTimer(self)
        self._timer.setInterval(int(engine.config.poll_interval * 1000))
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        events = self._engine.tick()
        self.changed.emit()
        if events:
            self.historyChanged.emit()

    # --- session state -------------------------------------------------

    @Property(bool, notify=changed)
    def inWorld(self) -> bool:
        return self._engine.state.in_world

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
        history = self._engine.history or History(data_dir() / "history.db")
        rows = []
        for visit in history.recent_visits(limit=100):
            duration = visit.duration_seconds
            rows.append(
                {
                    "when": visit.joined_at.astimezone().strftime("%Y-%m-%d %H:%M"),
                    "name": visit.world_name or visit.world_id,
                    "duration": f"{duration / 60:.0f}m" if duration else "now",
                    "peak": visit.peak_players,
                }
            )
        return rows

    @Property("QVariantList", notify=historyChanged)
    def historyTotals(self) -> list:
        history = self._engine.history or History(data_dir() / "history.db")
        totals = history.totals()
        return [
            {"label": "visits", "value": str(totals["visits"])},
            {"label": "worlds", "value": str(totals["unique_worlds"])},
            {"label": "hours", "value": f"{totals['seconds'] / 3600:.1f}"},
            {"label": "people met", "value": str(totals["people_met"])},
        ]

    def shutdown(self) -> None:
        self._timer.stop()
        self._engine.shutdown()
