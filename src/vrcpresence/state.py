from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .events import (
    Event,
    HeadsetMode,
    LeftRoom,
    LocalUser,
    PlayerJoin,
    PlayerLeave,
    WorldJoin,
    WorldName,
)


@dataclass
class SessionState:
    """Live picture of the current VRChat session, built from log events."""

    world_id: str | None = None
    instance_id: str | None = None
    world_name: str | None = None
    world_image_url: str | None = None
    world_capacity: int | None = None
    in_vr: bool | None = None
    players: list[str] = field(default_factory=list)
    joined_at: datetime | None = None
    local_user: str | None = None

    @property
    def in_world(self) -> bool:
        return self.world_id is not None

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def location(self) -> str | None:
        if self.world_id is None or self.instance_id is None:
            return None
        return f"{self.world_id}:{self.instance_id}"

    def apply(self, event: Event) -> None:
        if isinstance(event, WorldJoin):
            self.world_id = event.world_id
            self.instance_id = event.instance_id
            self.world_name = None
            self.world_image_url = None
            self.world_capacity = None
            self.players = []
            self.joined_at = datetime.now(timezone.utc)

        elif isinstance(event, WorldName):
            self.world_name = event.name

        elif isinstance(event, PlayerJoin):
            if event.display_name not in self.players:
                self.players.append(event.display_name)

        elif isinstance(event, PlayerLeave):
            if event.display_name in self.players:
                self.players.remove(event.display_name)

        elif isinstance(event, LeftRoom):
            self.world_id = None
            self.instance_id = None
            self.world_name = None
            self.world_image_url = None
            self.world_capacity = None
            self.players = []
            self.joined_at = None

        elif isinstance(event, HeadsetMode):
            self.in_vr = event.in_vr

        elif isinstance(event, LocalUser):
            self.local_user = event.display_name

    def apply_all(self, events: list[Event]) -> None:
        for event in events:
            self.apply(event)
