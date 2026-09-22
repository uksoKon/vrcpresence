"""Live heart rate from Pulsoid.

Needs an access token from https://pulsoid.net (Settings -> API -> tokens).
Whether that account needs to be paid is Pulsoid's own business decision,
not a technical restriction here - this connects with whatever token you
give it and simply won't receive data if your plan doesn't allow the feed.

Runs its own asyncio websocket connection on a background thread so it can
be driven from the engine's synchronous tick loop like everything else.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from dataclasses import dataclass

ENDPOINT = "wss://dev.pulsoid.net/api/v1/data/real_time"


def available() -> bool:
    try:
        import websockets  # noqa: F401
    except ImportError:
        return False
    return True


@dataclass
class HeartRateReading:
    bpm: int | None = None
    updated_at: float = 0.0

    @property
    def is_stale(self) -> bool:
        return self.bpm is None or time.monotonic() - self.updated_at > 30


class HeartRateClient:
    def __init__(self, token: str) -> None:
        self.token = token
        self.reading = HeartRateReading()
        self.connected = False
        self.last_error: str | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is not None or not self.token:
            return
        if not available():
            self.last_error = "websockets package is not installed"
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        self._thread = None
        self.connected = False

    def _run(self) -> None:
        try:
            asyncio.run(self._listen())
        except Exception as exc:  # noqa: BLE001 - background thread, surfaced as text
            self.last_error = str(exc)
            self.connected = False

    async def _listen(self) -> None:
        import websockets

        url = f"{ENDPOINT}?access_token={self.token}"
        while not self._stop.is_set():
            try:
                async with websockets.connect(url, open_timeout=10) as socket:
                    self.connected = True
                    self.last_error = None
                    while not self._stop.is_set():
                        message = await asyncio.wait_for(socket.recv(), timeout=5)
                        self._handle(message)
            except TimeoutError:
                continue
            except Exception as exc:  # noqa: BLE001 - retry loop, surfaced as text
                self.connected = False
                self.last_error = str(exc)
                if self._stop.is_set():
                    return
                await asyncio.sleep(5)

    def _handle(self, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return
        bpm = (payload.get("data") or {}).get("heartRate")
        if isinstance(bpm, (int, float)):
            self.reading = HeartRateReading(bpm=int(bpm), updated_at=time.monotonic())


def format_heart_rate(reading: HeartRateReading) -> str:
    if reading.is_stale or reading.bpm is None:
        return ""
    return f"♥ {reading.bpm} bpm"
