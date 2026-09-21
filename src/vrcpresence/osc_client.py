"""Sends text to VRChat's in-game chatbox over OSC.

This is the one thing VRChat's OSC API is genuinely good for. VRChat listens
on 127.0.0.1:9000 by default.
"""

from __future__ import annotations

from typing import Any

CHATBOX_INPUT = "/chatbox/input"
CHATBOX_TYPING = "/chatbox/typing"

# VRChat truncates anything longer than this.
MAX_CHATBOX_CHARS = 144


def format_chatbox_text(template: str, values: dict[str, str]) -> str:
    """Fill {tokens} in a status template and clamp to VRChat's limit.

    Unknown tokens are left as-is rather than raising, so a typo in a user's
    template degrades to visible text instead of killing the sender loop.
    """
    text = template
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text[:MAX_CHATBOX_CHARS]


class ChatboxClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9000) -> None:
        self.host = host
        self.port = port
        self._client: Any = None

    def _ensure_client(self) -> bool:
        if self._client is not None:
            return True
        try:
            from pythonosc.udp_client import SimpleUDPClient
        except ImportError:
            return False
        self._client = SimpleUDPClient(self.host, self.port)
        return True

    def send(self, text: str, *, notify: bool = False) -> bool:
        """Push text straight into the chatbox.

        notify=False keeps VRChat's notification sound silent, which is what
        you want for a status line that updates every few seconds.
        """
        if not self._ensure_client():
            return False
        try:
            self._client.send_message(CHATBOX_INPUT, [text[:MAX_CHATBOX_CHARS], True, notify])
        except OSError:
            return False
        return True

    def set_typing(self, typing: bool) -> bool:
        if not self._ensure_client():
            return False
        try:
            self._client.send_message(CHATBOX_TYPING, [typing])
        except OSError:
            return False
        return True

    def clear(self) -> bool:
        return self.send("")
