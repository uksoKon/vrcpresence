"""Is VRChat actually running right now?

Without this check the log alone is misleading: VRChat's last log file still
describes the last world you were in long after you quit, so replaying it
reports you as present in a world you left hours ago.
"""

from __future__ import annotations

from pathlib import Path

PROCESS_MARKERS = ("VRChat.exe", "vrchat.exe")


def vrchat_running() -> bool:
    """True when a VRChat process exists (it runs as VRChat.exe under Proton)."""
    proc = Path("/proc")
    if not proc.is_dir():
        return False

    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes()
        except (OSError, PermissionError):
            continue
        if not cmdline:
            continue
        text = cmdline.replace(b"\x00", b" ").decode("utf-8", errors="replace")
        if any(marker in text for marker in PROCESS_MARKERS):
            return True

    return False
