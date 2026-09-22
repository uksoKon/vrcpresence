"""Now-playing info for the chatbox, via MPRIS.

Shelling out to playerctl keeps this dependency-free and works with every
MPRIS player (Spotify, Firefox, VLC, mpv...). A browser tab counts as a
player, so preferred_players exists to keep a video from hijacking a status
line meant for music.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

FORMAT = "{{status}}\x1f{{artist}}\x1f{{title}}\x1f{{playerName}}\x1f{{position}}"
PREFERRED = ("spotify", "vlc", "mpv", "audacious", "elisa", "strawberry", "youtube-music")


@dataclass(frozen=True)
class NowPlaying:
    artist: str = ""
    title: str = ""
    player: str = ""
    playing: bool = False
    position: float = 0.0

    @property
    def is_empty(self) -> bool:
        return not self.title and not self.artist

    def format(self) -> str:
        if self.is_empty:
            return ""
        if self.artist and self.title:
            return f"{self.title} - {self.artist}"
        return self.title or self.artist


def available() -> bool:
    return shutil.which("playerctl") is not None


def _query(player: str | None = None) -> NowPlaying | None:
    command = ["playerctl"]
    if player:
        command += ["--player", player]
    command += ["metadata", "--format", FORMAT]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    parts = result.stdout.strip().split("\x1f")
    if len(parts) < 4:
        return None

    status, artist, title, name = parts[0], parts[1], parts[2], parts[3]
    # playerctl reports position in microseconds.
    raw_position = parts[4].strip() if len(parts) > 4 else ""
    try:
        position = float(raw_position) / 1_000_000 if raw_position else 0.0
    except ValueError:
        position = 0.0

    return NowPlaying(
        artist=artist.strip(),
        title=title.strip(),
        player=name.strip(),
        playing=status.strip().lower() == "playing",
        position=position,
    )


def now_playing(preferred_players: tuple[str, ...] = PREFERRED) -> NowPlaying:
    """Current track, preferring real music players over browser tabs."""
    if not available():
        return NowPlaying()

    try:
        listed = subprocess.run(
            ["playerctl", "-l"], capture_output=True, text=True, timeout=3, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return NowPlaying()

    players = [p.strip() for p in listed.stdout.splitlines() if p.strip()]

    for wanted in preferred_players:
        for player in players:
            if not player.lower().startswith(wanted):
                continue
            found = _query(player)
            if found and not found.is_empty:
                return found

    return _query() or NowPlaying()
