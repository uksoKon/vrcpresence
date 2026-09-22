"""Current conditions from Open-Meteo.

Open-Meteo needs no account and no API key. Coordinates are entered by the
user rather than guessed from their IP address, so nothing is looked up
about them without being asked. Results are cached hard - the weather does
not change on a chatbox refresh cycle.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

ENDPOINT = "https://api.open-meteo.com/v1/forecast"
CACHE_SECONDS = 600
TIMEOUT = 6

# https://open-meteo.com/en/docs - WMO weather codes, condensed.
CONDITIONS = {
    0: ("clear", "☀"),
    1: ("mostly clear", "☀"),
    2: ("partly cloudy", "⛅"),
    3: ("overcast", "☁"),
    45: ("fog", "░"),
    48: ("fog", "░"),
    51: ("drizzle", "☂"),
    53: ("drizzle", "☂"),
    55: ("drizzle", "☂"),
    61: ("rain", "☔"),
    63: ("rain", "☔"),
    65: ("heavy rain", "☔"),
    71: ("snow", "❄"),
    73: ("snow", "❄"),
    75: ("heavy snow", "❄"),
    80: ("showers", "☔"),
    81: ("showers", "☔"),
    82: ("showers", "☔"),
    95: ("thunderstorm", "⚡"),
    96: ("thunderstorm", "⚡"),
    99: ("thunderstorm", "⚡"),
}


@dataclass(frozen=True)
class Weather:
    temperature: float | None = None
    feels_like: float | None = None
    humidity: int | None = None
    wind: float | None = None
    code: int | None = None

    @property
    def is_empty(self) -> bool:
        return self.temperature is None

    @property
    def condition(self) -> str:
        return CONDITIONS.get(self.code, ("", ""))[0] if self.code is not None else ""

    @property
    def icon(self) -> str:
        return CONDITIONS.get(self.code, ("", ""))[1] if self.code is not None else ""

    def format(self) -> str:
        if self.is_empty:
            return ""
        icon = f"{self.icon} " if self.icon else ""
        return f"{icon}{self.temperature:.0f}°C"


class WeatherService:
    def __init__(self, latitude: float | None = None, longitude: float | None = None) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self._cached = Weather()
        self._fetched_at = 0.0

    @property
    def configured(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def current(self) -> Weather:
        if not self.configured:
            return Weather()

        now = time.monotonic()
        if self._cached and not self._cached.is_empty and now - self._fetched_at < CACHE_SECONDS:
            return self._cached
        if now - self._fetched_at < 60:
            return self._cached

        self._fetched_at = now
        self._cached = self._fetch() or self._cached
        return self._cached

    def _fetch(self) -> Weather | None:
        query = urllib.parse.urlencode(
            {
                "latitude": f"{self.latitude:.4f}",
                "longitude": f"{self.longitude:.4f}",
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                "wind_speed_10m,weather_code",
            }
        )
        try:
            with urllib.request.urlopen(f"{ENDPOINT}?{query}", timeout=TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

        current = payload.get("current") or {}
        if "temperature_2m" not in current:
            return None

        return Weather(
            temperature=current.get("temperature_2m"),
            feels_like=current.get("apparent_temperature"),
            humidity=current.get("relative_humidity_2m"),
            wind=current.get("wind_speed_10m"),
            code=current.get("weather_code"),
        )
