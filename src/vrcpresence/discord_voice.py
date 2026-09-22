"""Who's in your Discord voice channel, via a bot - not a self-bot.

Needs a bot token from https://discord.com/developers/applications, invited
to your server with the "Server Members" and "Voice States" privileged
intents enabled. This tracks channel membership and mute/deaf state through
the gateway; it does not join the voice channel itself.

Per-user "who is currently talking" needs the bot to actually join the
channel and decode raw voice packets - a much heavier and less stable
surface than gateway voice-state events, so it isn't included here.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


def available() -> bool:
    try:
        import discord  # noqa: F401
    except ImportError:
        return False
    return True


@dataclass(frozen=True)
class VoiceMember:
    name: str
    muted: bool = False
    deafened: bool = False


@dataclass
class VoiceChannelState:
    channel_name: str = ""
    members: list[VoiceMember] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.channel_name


class DiscordVoiceClient:
    """Runs a discord.py bot on a background thread, tracking one guild member's voice state."""

    def __init__(self, token: str, watch_user_id: str) -> None:
        self.token = token
        self.watch_user_id = watch_user_id
        self.state = VoiceChannelState()
        self.connected = False
        self.last_error: str | None = None
        self._thread: threading.Thread | None = None
        self._client = None

    def start(self) -> None:
        if self._thread is not None or not self.token:
            return
        if not available():
            self.last_error = "discord.py package is not installed"
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._client is not None:
            import asyncio

            try:
                loop = self._client.loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self._client.close(), loop)
            except Exception:  # noqa: BLE001 - shutdown path, never allowed to raise
                self.last_error = "voice client did not shut down cleanly"
        self._thread = None
        self.connected = False

    def _run(self) -> None:
        try:
            import discord
        except ImportError as exc:
            self.last_error = str(exc)
            return

        intents = discord.Intents.none()
        intents.guilds = True
        intents.voice_states = True
        intents.members = True

        client = discord.Client(intents=intents)
        self._client = client

        @client.event
        async def on_ready():
            self.connected = True
            self.last_error = None
            self._refresh_from_cache(discord, client)

        @client.event
        async def on_voice_state_update(member, before, after):
            watched = str(member.id) == self.watch_user_id
            in_tracked_channel = (after.channel and after.channel.name == self.state.channel_name) or (
                before.channel and before.channel.name == self.state.channel_name
            )
            if watched or in_tracked_channel:
                self._refresh_from_cache(discord, client)

        try:
            client.run(self.token, log_handler=None)
        except Exception as exc:  # noqa: BLE001 - background thread, surfaced as text
            self.last_error = str(exc)
            self.connected = False

    def _refresh_from_cache(self, discord, client) -> None:
        for guild in client.guilds:
            member = guild.get_member(int(self.watch_user_id))
            if member and member.voice and member.voice.channel:
                channel = member.voice.channel
                self.state = VoiceChannelState(
                    channel_name=channel.name,
                    members=[
                        VoiceMember(
                            name=m.display_name,
                            muted=bool(m.voice.self_mute or m.voice.mute),
                            deafened=bool(m.voice.self_deaf or m.voice.deaf),
                        )
                        for m in channel.members
                    ],
                )
                return
        self.state = VoiceChannelState()


def format_voice(state: VoiceChannelState) -> str:
    if state.is_empty:
        return ""
    return f"\U0001f399 {state.channel_name} · {len(state.members)}"
