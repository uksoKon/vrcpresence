"""Desktop notifications via notify-send.

Shelling out to notify-send avoids a D-Bus dependency and works on every
desktop that implements the notification spec.
"""

from __future__ import annotations

import shutil
import subprocess

APP_NAME = "vrcpresence"


def available() -> bool:
    return shutil.which("notify-send") is not None


def notify(summary: str, body: str = "", *, icon: str = "", urgency: str = "low") -> bool:
    if not available():
        return False

    command = ["notify-send", "--app-name", APP_NAME, "--urgency", urgency]
    if icon:
        command += ["--icon", icon]
    command += [summary]
    if body:
        command += [body]

    try:
        subprocess.run(command, check=False, capture_output=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return True
