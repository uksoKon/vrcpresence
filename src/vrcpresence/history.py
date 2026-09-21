"""Local SQLite record of where you've been and who was there.

Every VRChat companion tool shows you the present moment and forgets it a
second later. This keeps a private, local history so you can answer "what
was that world called" a week later.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,
    instance_id TEXT,
    world_name TEXT,
    joined_at TEXT NOT NULL,
    left_at TEXT,
    peak_players INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS encounters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL REFERENCES visits(id),
    display_name TEXT NOT NULL,
    seen_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_visits_joined_at ON visits(joined_at);
CREATE INDEX IF NOT EXISTS idx_encounters_visit ON encounters(visit_id);
"""


@dataclass
class Visit:
    id: int
    world_id: str
    world_name: str | None
    joined_at: datetime
    left_at: datetime | None
    peak_players: int

    @property
    def duration_seconds(self) -> float | None:
        if self.left_at is None:
            return None
        return (self.left_at - self.joined_at).total_seconds()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class History:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        self._open_visit_id: int | None = None
        self._close_orphans()

    def _close_orphans(self) -> None:
        """Close visits a previous run left open (crash, kill, stale session).

        Without this they render as "now" forever and inflate nothing but
        confusion. The real end time is unknowable, so the join time is used.
        """
        self._conn.execute("UPDATE visits SET left_at = joined_at WHERE left_at IS NULL")
        self._conn.commit()

    def clear(self) -> None:
        self._open_visit_id = None
        self._conn.execute("DELETE FROM encounters")
        self._conn.execute("DELETE FROM visits")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def start_visit(self, world_id: str, instance_id: str | None, world_name: str | None) -> int:
        self.end_visit()
        cursor = self._conn.execute(
            "INSERT INTO visits (world_id, instance_id, world_name, joined_at) VALUES (?, ?, ?, ?)",
            (world_id, instance_id, world_name, _now()),
        )
        self._conn.commit()
        self._open_visit_id = cursor.lastrowid
        return self._open_visit_id

    def set_world_name(self, name: str) -> None:
        if self._open_visit_id is None:
            return
        self._conn.execute(
            "UPDATE visits SET world_name = ? WHERE id = ?", (name, self._open_visit_id)
        )
        self._conn.commit()

    def record_player(self, display_name: str) -> None:
        if self._open_visit_id is None:
            return
        self._conn.execute(
            "INSERT INTO encounters (visit_id, display_name, seen_at) VALUES (?, ?, ?)",
            (self._open_visit_id, display_name, _now()),
        )
        self._conn.commit()

    def record_peak(self, player_count: int) -> None:
        if self._open_visit_id is None:
            return
        self._conn.execute(
            "UPDATE visits SET peak_players = MAX(peak_players, ?) WHERE id = ?",
            (player_count, self._open_visit_id),
        )
        self._conn.commit()

    def end_visit(self) -> None:
        if self._open_visit_id is None:
            return
        self._conn.execute(
            "UPDATE visits SET left_at = ? WHERE id = ? AND left_at IS NULL",
            (_now(), self._open_visit_id),
        )
        self._conn.commit()
        self._open_visit_id = None

    def recent_visits(self, limit: int = 50) -> list[Visit]:
        rows = self._conn.execute(
            "SELECT id, world_id, world_name, joined_at, left_at, peak_players "
            "FROM visits ORDER BY joined_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Visit(
                id=row[0],
                world_id=row[1],
                world_name=row[2],
                joined_at=_parse(row[3]),
                left_at=_parse(row[4]),
                peak_players=row[5],
            )
            for row in rows
        ]

    def people_met(self, limit: int = 50) -> list[tuple[str, int]]:
        """Who you run into most, by number of separate instances shared."""
        rows = self._conn.execute(
            "SELECT display_name, COUNT(DISTINCT visit_id) AS shared FROM encounters "
            "GROUP BY display_name ORDER BY shared DESC, display_name LIMIT ?",
            (limit,),
        ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def totals(self) -> dict[str, float | int]:
        row = self._conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT world_id) FROM visits"
        ).fetchone()
        seconds = 0.0
        for visit in self.recent_visits(limit=100000):
            seconds += visit.duration_seconds or 0.0
        return {
            "visits": row[0],
            "unique_worlds": row[1],
            "seconds": seconds,
            "people_met": len(self.people_met(limit=100000)),
        }
