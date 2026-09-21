from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldJoin:
    world_id: str
    instance_id: str
    raw_location: str


@dataclass(frozen=True)
class WorldName:
    name: str


@dataclass(frozen=True)
class PlayerJoin:
    display_name: str
    user_id: str | None = None


@dataclass(frozen=True)
class PlayerLeave:
    display_name: str
    user_id: str | None = None


@dataclass(frozen=True)
class LeftRoom:
    pass


@dataclass(frozen=True)
class HeadsetMode:
    """Whether this VRChat session launched into VR or desktop mode."""

    in_vr: bool


Event = WorldJoin | WorldName | PlayerJoin | PlayerLeave | LeftRoom | HeadsetMode
