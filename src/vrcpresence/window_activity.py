"""What you're focused on, for the "on desktop in Blender" style status.

Window titles regularly contain document names, video titles and private
conversations, so this reports the application by default and only includes
the title when explicitly asked for - and never for apps on the blocklist.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass

DEFAULT_BLOCKED = ("keepassxc", "bitwarden", "1password", "gnome-keyring", "polkit")


@dataclass(frozen=True)
class ActiveWindow:
    app: str = ""
    title: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.app and not self.title


def _run(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


def _hyprland() -> ActiveWindow | None:
    if not shutil.which("hyprctl"):
        return None
    output = _run(["hyprctl", "activewindow", "-j"])
    if not output.strip():
        return None
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return None
    return ActiveWindow(app=data.get("class", ""), title=data.get("title", ""))


def _sway() -> ActiveWindow | None:
    if not shutil.which("swaymsg"):
        return None
    output = _run(["swaymsg", "-t", "get_tree"])
    if not output.strip():
        return None
    try:
        tree = json.loads(output)
    except json.JSONDecodeError:
        return None

    stack = [tree]
    while stack:
        node = stack.pop()
        if node.get("focused") and node.get("name"):
            app = node.get("app_id") or (node.get("window_properties") or {}).get("class") or ""
            return ActiveWindow(app=app, title=node.get("name", ""))
        stack.extend(node.get("nodes", []) + node.get("floating_nodes", []))
    return None


def _x11() -> ActiveWindow | None:
    if not shutil.which("xdotool") or not os.environ.get("DISPLAY"):
        return None
    title = _run(["xdotool", "getactivewindow", "getwindowname"]).strip()
    app = _run(["xdotool", "getactivewindow", "getwindowclassname"]).strip()
    if not title and not app:
        return None
    return ActiveWindow(app=app, title=title)


def active_window() -> ActiveWindow:
    for probe in (_hyprland, _sway, _x11):
        found = probe()
        if found and not found.is_empty:
            return found
    return ActiveWindow()


def describe(
    window: ActiveWindow,
    *,
    show_title: bool = False,
    blocked: tuple[str, ...] = DEFAULT_BLOCKED,
) -> str:
    """Render the focused app, respecting the privacy blocklist."""
    if window.is_empty:
        return ""

    haystack = f"{window.app} {window.title}".lower()
    if any(term and term in haystack for term in blocked):
        return ""

    app = window.app or window.title
    if not show_title or not window.title:
        return app
    return f"{app}: {window.title}"
