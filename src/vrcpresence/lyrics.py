"""Synced lyrics from LRCLIB, lined up with playback position.

LRCLIB is free and needs no account. A track is looked up once and its
timed lines cached, then the current line is picked locally from the
playback position - so scrolling lyrics cost one request per song, not one
per chatbox refresh.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

ENDPOINT = "https://lrclib.net/api/get"
TIMEOUT = 6
USER_AGENT = "vrcpresence (https://github.com/uksoKon/vrcpresence)"

LINE = re.compile(r"\[(\d+):(\d+)(?:\.(\d+))?\]\s*(.*)")


@dataclass(frozen=True)
class TimedLine:
    at: float
    text: str


def parse_lrc(body: str) -> list[TimedLine]:
    """Parse an .lrc body into timed lines, skipping blank ones."""
    lines: list[TimedLine] = []
    for raw in body.splitlines():
        match = LINE.match(raw.strip())
        if not match:
            continue
        minutes, seconds, fraction, text = match.groups()
        at = int(minutes) * 60 + int(seconds)
        if fraction:
            at += int(fraction) / (10 ** len(fraction))
        if text.strip():
            lines.append(TimedLine(at=at, text=text.strip()))
    return sorted(lines, key=lambda line: line.at)


def line_at(lines: list[TimedLine], position: float) -> str:
    """The lyric being sung at this position."""
    current = ""
    for line in lines:
        if line.at > position:
            break
        current = line.text
    return current


class LyricsService:
    def __init__(self) -> None:
        self._key: tuple[str, str] | None = None
        self._lines: list[TimedLine] = []
        self._failed: set[tuple[str, str]] = set()

    @property
    def has_lyrics(self) -> bool:
        return bool(self._lines)

    def line_for(self, artist: str, title: str, position: float) -> str:
        """Current lyric for a track, fetching it the first time it is seen."""
        if not artist or not title:
            return ""

        key = (artist.lower(), title.lower())
        if key in self._failed:
            return ""

        if key != self._key:
            self._key = key
            self._lines = self._fetch(artist, title) or []
            if not self._lines:
                self._failed.add(key)
                return ""

        return line_at(self._lines, position)

    def _fetch(self, artist: str, title: str) -> list[TimedLine] | None:
        query = urllib.parse.urlencode({"artist_name": artist, "track_name": title})
        request = urllib.request.Request(
            f"{ENDPOINT}?{query}", headers={"User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

        synced = payload.get("syncedLyrics")
        return parse_lrc(synced) if synced else None
