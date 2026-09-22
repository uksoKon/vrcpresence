"""Turns the current machine and session state into chatbox components.

Kept apart from the engine so each source can be tested on its own and the
assembly order lives in one readable place.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .builder import Component
from .config import Config, config_dir
from .discord_voice import DiscordVoiceClient, format_voice
from .lyrics import LyricsService
from .media import NowPlaying
from .openvr_source import format_battery, format_performance
from .openvr_source import read as read_openvr
from .pulsoid import HeartRateClient, format_heart_rate
from .spotify import SpotifyClient, format_track
from .state import SessionState
from .sysinfo import CpuUsage, GpuReading, NetworkRate, cpu_temperature, gpu_reading, memory_usage
from .tiktok_live import TikTokLiveClient
from .tiktok_live import format_status as format_tiktok
from .twitch import TwitchClient
from .weather import Weather, WeatherService
from .window_activity import active_window, describe

# Higher survives longer when the line is too long for VRChat's 144 chars.
PRIORITY = {
    "status": 95,
    "world": 90,
    "music": 80,
    "lyrics": 70,
    "heart_rate": 65,
    "time": 60,
    "weather": 50,
    "spotify": 45,
    "system": 40,
    "tracker_battery": 38,
    "vr_performance": 36,
    "network": 30,
    "window": 20,
    "twitch": 15,
    "tiktok": 15,
    "discord_voice": 10,
}


@dataclass
class ComponentSources:
    """Holds the samplers that need previous readings to compute a rate, and
    the background-threaded service clients (Pulsoid, TikTok, Discord voice).

    Clients for services that need credentials only start if those
    credentials are present at startup. Adding credentials later needs a
    restart to take effect - except Spotify, which is always a manual login
    action anyway and reconnects immediately.
    """

    cpu: CpuUsage
    network: NetworkRate
    weather: WeatherService
    lyrics: LyricsService
    heart_rate: HeartRateClient | None = None
    tiktok: TikTokLiveClient | None = None
    discord_voice: DiscordVoiceClient | None = None
    spotify: SpotifyClient | None = None
    twitch: TwitchClient | None = None
    _window: str = ""
    _window_at: float = 0.0
    _openvr_cache: tuple | None = None
    _openvr_at: float = 0.0

    def window(self, *, show_title: bool) -> str:
        """Cached: reading the focused window shells out to the compositor."""
        now = time.monotonic()
        if now - self._window_at < 3.0:
            return self._window
        self._window_at = now
        self._window = describe(active_window(), show_title=show_title)
        return self._window

    def openvr(self) -> tuple:
        """Cached: an OpenVR read initializes and shuts down the API each call."""
        now = time.monotonic()
        if self._openvr_cache is not None and now - self._openvr_at < 15.0:
            return self._openvr_cache
        self._openvr_at = now
        reading = read_openvr()
        self._openvr_cache = (format_battery(reading.devices), format_performance(reading.performance))
        return self._openvr_cache

    @classmethod
    def create(cls, config: Config, *, token_dir: Path | None = None) -> ComponentSources:
        sources = cls(
            cpu=CpuUsage(),
            network=NetworkRate(),
            weather=WeatherService(config.weather_latitude, config.weather_longitude),
            lyrics=LyricsService(),
        )

        if config.show_heart_rate and config.pulsoid_token:
            sources.heart_rate = HeartRateClient(config.pulsoid_token)
            sources.heart_rate.start()

        if config.show_tiktok and config.tiktok_username:
            sources.tiktok = TikTokLiveClient(config.tiktok_username)
            sources.tiktok.start()

        if config.show_discord_voice and config.discord_bot_token and config.discord_watch_user_id:
            sources.discord_voice = DiscordVoiceClient(
                config.discord_bot_token, config.discord_watch_user_id
            )
            sources.discord_voice.start()

        if config.show_spotify and config.spotify_client_id:
            path = (token_dir or config_dir()) / "spotify.json"
            sources.spotify = SpotifyClient(config.spotify_client_id, path)

        if config.show_twitch and config.twitch_client_id and config.twitch_client_secret:
            sources.twitch = TwitchClient(
                config.twitch_client_id, config.twitch_client_secret, config.twitch_username
            )

        return sources

    def shutdown(self) -> None:
        if self.heart_rate:
            self.heart_rate.stop()
        if self.tiktok:
            self.tiktok.stop()
        if self.discord_voice:
            self.discord_voice.stop()


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

    spotify_track = sources.spotify.now_playing() if sources.spotify and sources.spotify.authenticated else None

    if spotify_track and not spotify_track.is_empty:
        add("spotify", format_track(spotify_track, config.spotify_template))
        if config.show_lyrics and spotify_track.is_playing:
            add(
                "lyrics",
                sources.lyrics.line_for(
                    spotify_track.artist, spotify_track.title, spotify_track.progress_seconds
                ),
            )
    elif config.chatbox_media and not track.is_empty:
        add("music", f"♪ {track.format()}")
        if config.show_lyrics and track.playing:
            add("lyrics", sources.lyrics.line_for(track.artist, track.title, track.position))

    if config.show_heart_rate and sources.heart_rate:
        add(
            "heart_rate",
            format_heart_rate(sources.heart_rate.reading),
            in_vr=config.heart_rate_in_vr,
            on_desktop=config.heart_rate_on_desktop,
        )

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

    if config.show_tracker_battery or config.show_vr_performance:
        battery_text, performance_text = sources.openvr()
        if config.show_tracker_battery:
            add("tracker_battery", battery_text, in_vr=config.vr_in_vr, on_desktop=config.vr_on_desktop)
        if config.show_vr_performance:
            add("vr_performance", performance_text, in_vr=config.vr_in_vr, on_desktop=config.vr_on_desktop)

    if config.show_twitch and sources.twitch:
        add("twitch", sources.twitch.current().format())

    if config.show_tiktok and sources.tiktok:
        add("tiktok", format_tiktok(sources.tiktok.state))

    if config.show_discord_voice and sources.discord_voice:
        add("discord_voice", format_voice(sources.discord_voice.state))

    return components
