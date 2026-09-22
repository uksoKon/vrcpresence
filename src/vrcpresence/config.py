from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "vrcpresence"


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    return Path(base) / "vrcpresence"


@dataclass
class Config:
    discord_enabled: bool = True
    discord_app_id: str = ""
    show_players: bool = True
    allow_join: bool = True
    private_mode: bool = False
    hide_private_instances: bool = False

    chatbox_enabled: bool = False
    chatbox_templates: list[str] = field(default_factory=lambda: ["{world} | {players} here"])
    chatbox_interval: int = 8
    chatbox_media: bool = True
    chatbox_typing: bool = False
    # Assemble the line from components instead of a single template.
    chatbox_components: bool = False

    # Each component: enabled, plus where it shows. Separate VR/desktop
    # switches mean rig stats at your desk and music in the headset.
    show_world: bool = True
    world_in_vr: bool = True
    world_on_desktop: bool = True

    show_time: bool = False
    time_in_vr: bool = True
    time_on_desktop: bool = True

    show_weather: bool = False
    weather_latitude: float | None = None
    weather_longitude: float | None = None

    show_system: bool = False
    system_in_vr: bool = False
    system_on_desktop: bool = True

    show_network: bool = False
    network_in_vr: bool = False
    network_on_desktop: bool = True

    show_window: bool = False
    window_titles: bool = False
    window_in_vr: bool = False
    window_on_desktop: bool = True

    show_lyrics: bool = False
    show_status: bool = False
    personal_status: str = ""

    notifications_enabled: bool = True
    history_enabled: bool = True
    # History lives only as long as the VRChat session: closing VRChat wipes
    # it, so nothing accumulates on disk between sessions.
    session_history_only: bool = True
    poll_interval: float = 2.0

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        path = path or (config_dir() / "config.json")
        if not path.is_file():
            return cls()
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return cls()
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path: Path | None = None) -> None:
        path = path or (config_dir() / "config.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))
