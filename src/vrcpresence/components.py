"""Turns the current machine and session state into chatbox components.

Kept apart from the engine so each source can be tested on its own and the
assembly order lives in one readable place.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

from .builder import Component
from .config import Config
from .lyrics import LyricsService
from .media import NowPlaying
from .state import SessionState
from .sysinfo import CpuUsage, GpuReading, NetworkRate, cpu_temperature, gpu_reading, memory_usage
from .weather import Weather, WeatherService
from .window_activity import active_window, describe

# Higher survives longer when the line is too long for VRChat's 144 chars.
PRIORITY = {
    "status": 95,
    "world": 90,
    "music": 80,
    "lyrics": 70,
    "time": 60,
    "weather": 50,
    "system": 40,
    "network": 30,
    "window": 20,
}


@dataclass
class ComponentSources:
    """Holds the samplers that need previous readings to compute a rate."""

    cpu: CpuUsage
    network: NetworkRate
    weather: WeatherService
    lyrics: LyricsService
    _window: str = ""
    _window_at: float = 0.0

    def window(self, *, show_title: bool) -> str:
        """Cached: reading the focused window shells out to the compositor."""
        now = time.monotonic()
        if now - self._window_at < 3.0:
            return self._window
        self._window_at = now
        self._window = describe(active_window(), show_title=show_title)
        return self._window

    @classmethod
    def create(cls, config: Config) -> ComponentSources:
        return cls(
            cpu=CpuUsage(),
            network=NetworkRate(),
            weather=WeatherService(config.weather_latitude, config.weather_longitude),
            lyrics=LyricsService(),
        )


def world_text(state: SessionState, running: bool) -> str:
    if not running:
        return ""
    if not state.in_world:
        return "loading"
    name = state.world_name or "a world"
    if state.world_capacity:
        return f"{name} ({state.player_count}/{state.world_capacity})"
    return f"{name} ({state.player_count})"


def system_text(cpu: float | None, memory: float | None, gpu: GpuReading, temp: float | None) -> str:
    parts = []
    if cpu is not None:
        parts.append(f"CPU {cpu:.0f}%")
    if temp is not None:
        parts.append(f"{temp:.0f}°C")
    if gpu.usage is not None:
        parts.append(f"GPU {gpu.usage:.0f}%")
    elif gpu.temperature is not None:
        parts.append(f"GPU {gpu.temperature:.0f}°C")
    if memory is not None:
        parts.append(f"RAM {memory:.0f}%")
    return " ".join(parts)


def network_text(rates: tuple[float, float] | None) -> str:
    if rates is None:
        return ""
    down, up = rates
    return f"↓{down:.0f} ↑{up:.0f} Mbps"


def weather_text(weather: Weather) -> str:
    return weather.format()


def collect(
    config: Config,
    state: SessionState,
    sources: ComponentSources,
    *,
    running: bool,
    track: NowPlaying,
) -> list[Component]:
    """Every enabled component, in display order."""
    components: list[Component] = []

    def add(key: str, text: str, *, in_vr: bool = True, on_desktop: bool = True) -> None:
        if text:
            components.append(
                Component(
                    key=key,
                    text=text,
                    priority=PRIORITY.get(key, 50),
                    in_vr=in_vr,
                    on_desktop=on_desktop,
                )
            )

    if config.show_status and config.personal_status:
        add("status", config.personal_status.strip())

    if config.show_world:
        add(
            "world",
            world_text(state, running),
            in_vr=config.world_in_vr,
            on_desktop=config.world_on_desktop,
        )

    if config.chatbox_media and not track.is_empty:
        add("music", f"♪ {track.format()}")

        if config.show_lyrics and track.playing:
            add("lyrics", sources.lyrics.line_for(track.artist, track.title, track.position))

    if config.show_time:
        now = datetime.now().astimezone()
        add(
            "time",
            f"{now:%H:%M} {now.tzname() or ''}".strip(),
            in_vr=config.time_in_vr,
            on_desktop=config.time_on_desktop,
        )

    if config.show_weather:
        add("weather", weather_text(sources.weather.current()))

    if config.show_system:
        add(
            "system",
            system_text(sources.cpu.read(), memory_usage(), gpu_reading(), cpu_temperature()),
            in_vr=config.system_in_vr,
            on_desktop=config.system_on_desktop,
        )

    if config.show_network:
        add(
            "network",
            network_text(sources.network.read()),
            in_vr=config.network_in_vr,
            on_desktop=config.network_on_desktop,
        )

    if config.show_window:
        add(
            "window",
            sources.window(show_title=config.window_titles),
            in_vr=config.window_in_vr,
            on_desktop=config.window_on_desktop,
        )

    return components
