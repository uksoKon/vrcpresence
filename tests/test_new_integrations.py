import json
import time
from unittest.mock import MagicMock, patch

from vrcpresence.discord_voice import VoiceChannelState, VoiceMember, format_voice
from vrcpresence.intellichat import IntelliChatConfig, IntelliChatService
from vrcpresence.pulsoid import HeartRateReading, format_heart_rate
from vrcpresence.spotify import SpotifyTrack, _pkce_pair, format_track
from vrcpresence.tiktok_live import TikTokState, format_status
from vrcpresence.tts import speak
from vrcpresence.twitch import TwitchStatus

# --- twitch ------------------------------------------------------------


def test_twitch_status_format_when_offline():
    assert TwitchStatus(is_live=False).format() == ""


def test_twitch_status_format_when_live():
    status = TwitchStatus(is_live=True, category="Just Chatting", viewer_count=42, follower_count=100)
    text = status.format()
    assert "Just Chatting" in text
    assert "42 viewers" in text
    assert "100 followers" in text


# --- spotify -------------------------------------------------------------


def test_pkce_pair_is_url_safe_and_distinct():
    v1, c1 = _pkce_pair()
    v2, c2 = _pkce_pair()
    assert v1 != v2
    assert c1 != c2
    assert all(ch not in v1 for ch in "+/=")
    assert all(ch not in c1 for ch in "+/=")
    assert all(ch not in c2 for ch in "+/=")


def test_spotify_track_format():
    track = SpotifyTrack(title="Song", artist="Artist")
    assert format_track(track) == "Song - Artist"


def test_spotify_track_format_marks_explicit():
    track = SpotifyTrack(title="Song", artist="Artist", explicit=True)
    assert format_track(track).startswith("\U0001f51e")


def test_spotify_track_empty_format():
    assert format_track(SpotifyTrack()) == ""


# --- pulsoid ---------------------------------------------------------------


def test_heart_rate_reading_stale_by_default():
    assert HeartRateReading().is_stale


def test_heart_rate_reading_fresh():
    reading = HeartRateReading(bpm=80, updated_at=time.monotonic())
    assert not reading.is_stale
    assert format_heart_rate(reading) == "♥ 80 bpm"


def test_heart_rate_format_empty_when_stale():
    old = HeartRateReading(bpm=80, updated_at=time.monotonic() - 999)
    assert format_heart_rate(old) == ""


# --- tiktok ------------------------------------------------------------------


def test_tiktok_format_when_offline():
    assert format_status(TikTokState(is_live=False)) == ""


def test_tiktok_format_when_live_with_event():
    state = TikTokState(is_live=True, viewer_count=12, recent_events=["a followed"])
    text = format_status(state)
    assert "12 watching" in text
    assert "a followed" in text


# --- discord voice -----------------------------------------------------------


def test_voice_state_empty_by_default():
    assert VoiceChannelState().is_empty


def test_format_voice():
    state = VoiceChannelState(channel_name="Lounge", members=[VoiceMember("a"), VoiceMember("b")])
    assert format_voice(state) == "\U0001f399 Lounge · 2"


def test_format_voice_empty():
    assert format_voice(VoiceChannelState()) == ""


# --- tts ---------------------------------------------------------------------


def test_speak_returns_false_with_no_engine(monkeypatch):
    monkeypatch.setattr("vrcpresence.tts.available_engine", lambda: None)
    assert speak("hello") is False


def test_speak_returns_false_for_blank_text():
    assert speak("   ") is False


def test_speak_launches_engine(monkeypatch):
    monkeypatch.setattr("vrcpresence.tts.available_engine", lambda: "espeak-ng")
    with patch("vrcpresence.tts.subprocess.Popen") as popen:
        assert speak("hello there") is True
        popen.assert_called_once()
        assert popen.call_args[0][0] == ["espeak-ng", "hello there"]


# --- intellichat ---------------------------------------------------------------


def test_intellichat_disabled_returns_original_text():
    service = IntelliChatService()
    config = IntelliChatConfig(enabled=False, api_key="x")
    assert service.process("hello wrold", config, limit=144) == "hello wrold"


def test_intellichat_without_key_returns_original_text():
    service = IntelliChatService()
    config = IntelliChatConfig(enabled=True, api_key="")
    assert service.process("hello wrold", config, limit=144) == "hello wrold"


def test_intellichat_returns_original_immediately_then_caches_result():
    service = IntelliChatService()
    config = IntelliChatConfig(enabled=True, api_key="test-key")

    response_body = json.dumps(
        {"choices": [{"message": {"content": "hello world"}}]}
    ).encode()

    mock_response = MagicMock()
    mock_response.read.return_value = response_body
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("vrcpresence.intellichat.urllib.request.urlopen", return_value=mock_response):
        first = service.process("hello wrold", config, limit=144)
        assert first == "hello wrold"  # immediate: background thread hasn't finished

        for _ in range(50):
            if service.process("hello wrold", config, limit=144) == "hello world":
                break
            time.sleep(0.05)

    assert service.process("hello wrold", config, limit=144) == "hello world"


def test_intellichat_network_failure_falls_back_to_original():
    service = IntelliChatService()
    config = IntelliChatConfig(enabled=True, api_key="test-key")

    with patch("vrcpresence.intellichat.urllib.request.urlopen", side_effect=OSError("down")):
        result = service.process("hello wrold", config, limit=144)
        assert result == "hello wrold"
        time.sleep(0.2)
        assert service.process("hello wrold", config, limit=144) == "hello wrold"
