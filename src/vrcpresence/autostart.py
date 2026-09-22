"""Launch on login, via a standard XDG autostart .desktop entry.

Every major Linux desktop (GNOME, KDE, Hyprland+xdg-desktop-portal via
dbus-launch session managers, etc.) reads ~/.config/autostart/*.desktop on
session start - this needs no desktop-specific integration.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

DESKTOP_FILE = "vrcpresence.desktop"

ENTRY = """[Desktop Entry]
Type=Application
Name=vrcpresence
Comment=VRChat status, Discord presence and chatbox
Exec={exec_line}
Terminal=false
X-GNOME-Autostart-enabled=true
"""


def _autostart_dir() -> Path:
    import os

    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "autostart"


def _exec_line() -> str:
    binary = shutil.which("vrcpresence")
    if binary:
        return f"{binary} run --chatbox"
    return f"{sys.executable} -m vrcpresence run --chatbox"


def enable() -> Path:
    directory = _autostart_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / DESKTOP_FILE
    path.write_text(ENTRY.format(exec_line=_exec_line()))
    return path


def disable() -> None:
    path = _autostart_dir() / DESKTOP_FILE
    path.unlink(missing_ok=True)


def is_enabled() -> bool:
    return (_autostart_dir() / DESKTOP_FILE).is_file()
