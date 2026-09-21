"""Follows the desktop's own colour palette instead of inventing one.

Serpantinum (and anything else writing the same settings file) keeps the
active palette, font and corner radius in a JSON file, regenerated whenever
the wallpaper or preset changes - including by matugen. Reading it means the
app matches the rest of the desktop automatically, and keeps matching after a
theme switch, rather than drifting into its own look.

Falls back to a built-in palette when that file isn't present, so this works
on any desktop.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SETTINGS_PATH = Path.home() / ".config" / "serpantinum" / "settings.json"

BUILT_IN = {
    "base": "#0d0f14",
    "mantle": "#11131a",
    "surface0": "#171a23",
    "surface1": "#20242f",
    "surface2": "#2b303d",
    "overlay1": "#5c6274",
    "text": "#e6e8f0",
    "subtext0": "#8d93a6",
    "mauve": "#b36ce8",
    "green": "#7ddba0",
    "yellow": "#e8c37d",
    "red": "#e8737d",
}

DEFAULT_FONT = "monospace"
DEFAULT_RADIUS = 14


@dataclass(frozen=True)
class DesktopTheme:
    colors: dict[str, str] = field(default_factory=lambda: dict(BUILT_IN))
    font_family: str = DEFAULT_FONT
    radius: int = DEFAULT_RADIUS
    preset: str = "built-in"
    source: Path | None = None

    def color(self, name: str, fallback: str = "#ffffff") -> str:
        value = self.colors.get(name)
        if isinstance(value, str) and value.startswith("#"):
            return value
        return BUILT_IN.get(name, fallback)

    @property
    def following_desktop(self) -> bool:
        return self.source is not None


def load_desktop_theme(path: Path | None = None) -> DesktopTheme:
    path = path or SETTINGS_PATH
    if not path.is_file():
        return DesktopTheme()

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return DesktopTheme()

    theme = data.get("theme")
    if not isinstance(theme, dict):
        return DesktopTheme()

    colors = dict(BUILT_IN)
    for key, value in (theme.get("colors") or {}).items():
        if isinstance(value, str) and value.startswith("#"):
            colors[key] = value

    font = theme.get("fontFamily")
    radius = theme.get("borderRadius")

    return DesktopTheme(
        colors=colors,
        font_family=font if isinstance(font, str) and font else DEFAULT_FONT,
        # Serpantinum allows a very round 29px; clamped so the app stays usable
        # at either extreme of its slider.
        radius=max(0, min(int(radius), 28)) if isinstance(radius, (int, float)) else DEFAULT_RADIUS,
        preset=theme.get("activePreset") or "custom",
        source=path,
    )
