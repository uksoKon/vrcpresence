"""Reads VRChat's own log files to learn what OSC cannot tell us.

VRChat's OSC API only exposes avatar parameters, input and the chatbox. It
does not expose which world you're in, who is in the instance with you, or
whether you're in VR - that information only exists in VRChat's log file.
This module tails that log.

VRChat starts a NEW log file every launch, so a watcher that opens one file
once stops working the moment you restart the game. `LogWatcher` re-scans
for a newer file on every poll and follows the rotation.

The patterns below are the part most likely to drift: VRChat's log format
isn't documented or guaranteed stable. Run `vrcpresence calibrate` against a
real log to verify them after a VRChat update - every pattern lives in
PATTERNS so a fix is a one-line change.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

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

VRCHAT_STEAM_APPID = "438100"

PATTERNS = {
    "world_join": re.compile(r"\[Behaviour\] Joining (wrld_[0-9a-fA-F-]+):(\S+)"),
    "world_name": re.compile(r"\[Behaviour\] Joining or Creating Room: (.+?)\s*$"),
    "player_join": re.compile(r"\[Behaviour\] OnPlayerJoined\s+(.+?)(?:\s+\((usr_[0-9a-fA-F-]+)\))?\s*$"),
    "player_leave": re.compile(r"\[Behaviour\] OnPlayerLeft\s+(.+?)(?:\s+\((usr_[0-9a-fA-F-]+)\))?\s*$"),
    "left_room": re.compile(r"\[Behaviour\] OnLeftRoom"),
    "local_user": re.compile(r"User Authenticated:\s+(.+?)(?:\s+\((usr_[0-9a-fA-F-]+)\))?\s*$"),
    # Desktop is detectable two ways, both verified against a real log: the
    # --no-vr launch flag, and VRChat's XR stack failing to come up (which is
    # what happens when no headset is connected).
    "desktop_mode": re.compile(
        r"Arg:\s*--no-vr\b"
        r"|\[OpenVR\].{0,20}Could not initialize"
        r"|\[SteamVR\].{0,20}Initialization failed"
    ),
    # Not yet confirmed against a VR session log - run `vrcpresence calibrate`
    # after playing in VR and check the reported mode.
    "vr_mode": re.compile(r"\[OpenVR\].{0,20}Initialized|\[SteamVR\].{0,20}Initialized\s*$"),
}

# Lines worth showing the user when mode detection comes up empty.
XR_HINT = re.compile(r"OpenVR|SteamVR|\bXR\b|HMD|Oculus", re.IGNORECASE)


def parse_line(line: str) -> Event | None:
    """Turn one raw log line into an event, or None if it isn't interesting."""
    if match := PATTERNS["world_join"].search(line):
        world_id, instance_id = match.group(1), match.group(2)
        return WorldJoin(
            world_id=world_id,
            instance_id=instance_id,
            raw_location=f"{world_id}:{instance_id}",
        )

    if match := PATTERNS["world_name"].search(line):
        return WorldName(name=match.group(1))

    if match := PATTERNS["player_join"].search(line):
        return PlayerJoin(display_name=match.group(1), user_id=match.group(2))

    if match := PATTERNS["player_leave"].search(line):
        return PlayerLeave(display_name=match.group(1), user_id=match.group(2))

    if PATTERNS["left_room"].search(line):
        return LeftRoom()

    if match := PATTERNS["local_user"].search(line):
        return LocalUser(display_name=match.group(1), user_id=match.group(2))

    if PATTERNS["desktop_mode"].search(line):
        return HeadsetMode(in_vr=False)

    if PATTERNS["vr_mode"].search(line):
        return HeadsetMode(in_vr=True)

    return None


def parse_lines(lines: Iterator[str]) -> Iterator[Event]:
    for line in lines:
        if event := parse_line(line):
            yield event


def steam_library_roots() -> list[Path]:
    """Every Steam library on this machine, including extra drives.

    Games get installed on a second drive constantly, and a tool that only
    looks in ~/.steam finds nothing for those users.
    """
    roots: list[Path] = []
    bases = [
        Path.home() / ".steam" / "steam",
        Path.home() / ".local" / "share" / "Steam",
        Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
    ]

    for base in bases:
        if base.is_dir() and base not in roots:
            roots.append(base)

        vdf = base / "steamapps" / "libraryfolders.vdf"
        if not vdf.is_file():
            continue
        for match in re.finditer(r'"path"\s*"([^"]+)"', vdf.read_text(errors="replace")):
            extra = Path(match.group(1))
            if extra.is_dir() and extra not in roots:
                roots.append(extra)

    return roots


def find_log_dir() -> Path | None:
    """Locate VRChat's log directory inside its Proton prefix."""
    suffix = Path("steamapps/compatdata") / VRCHAT_STEAM_APPID / "pfx/drive_c/users/steamuser"
    for root in steam_library_roots():
        for appdata in ("AppData/LocalLow", "AppData/Local Settings/Application Data"):
            candidate = root / suffix / appdata / "VRChat" / "VRChat"
            if candidate.is_dir():
                return candidate
    return None


def find_latest_log(log_dir: Path) -> Path | None:
    logs = sorted(log_dir.glob("output_log_*.txt"), key=lambda p: p.stat().st_mtime)
    return logs[-1] if logs else None


class LogWatcher:
    """Follows the newest VRChat log file, surviving game restarts."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self.log_dir = log_dir
        self._current: Path | None = None
        self._position = 0

    @property
    def current_log(self) -> Path | None:
        return self._current

    def poll(self) -> list[Event]:
        """Read whatever is new since the last poll.

        Switching to a newly created log file (VRChat was restarted) replays
        that file from the top, so a session that began before we started
        watching is still picked up in full.
        """
        log_dir = self.log_dir or find_log_dir()
        if log_dir is None or not log_dir.is_dir():
            return []

        latest = find_latest_log(log_dir)
        if latest is None:
            return []

        if latest != self._current:
            self._current = latest
            self._position = 0

        try:
            size = latest.stat().st_size
        except OSError:
            return []

        if size < self._position:
            # File was truncated or replaced in place; start over.
            self._position = 0

        if size == self._position:
            return []

        with latest.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(self._position)
            chunk = f.read()
            self._position = f.tell()

        return list(parse_lines(iter(chunk.splitlines())))
