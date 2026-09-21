from pathlib import Path

from vrcpresence.config import Config
from vrcpresence.engine import Engine
from vrcpresence.events import LocalUser
from vrcpresence.log_watcher import LogWatcher, parse_line
from vrcpresence.media import NowPlaying
from vrcpresence.state import SessionState

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_local_user():
    line = (
        "2026.09.21 15:06:04 Debug      -  User Authenticated: ukso "
        "(usr_c32ce178-4160-4c14-bf03-db851a63f0d7)"
    )
    event = parse_line(line)
    assert isinstance(event, LocalUser)
    assert event.display_name == "ukso"
    assert event.user_id == "usr_c32ce178-4160-4c14-bf03-db851a63f0d7"


def test_state_remembers_local_user():
    state = SessionState()
    state.apply(LocalUser(display_name="ukso"))
    assert state.local_user == "ukso"


def _engine(tmp_path, monkeypatch, *, session_only=True, running=True) -> Engine:
    # engine.py imports data_dir directly, so patch it there.
    monkeypatch.setattr("vrcpresence.engine.data_dir", lambda: tmp_path)
    body = (
        "2026.09.21 15:06:04 Debug - User Authenticated: ukso (usr_abc)\n"
        + (FIXTURES / "session.log").read_text()
    )
    (tmp_path / "output_log_00.txt").write_text(body)

    config = Config(
        discord_enabled=False,
        chatbox_enabled=False,
        notifications_enabled=False,
        history_enabled=True,
        session_history_only=session_only,
    )
    return Engine(config, log_watcher=LogWatcher(log_dir=tmp_path), is_running=lambda: running)


def test_you_are_not_counted_as_someone_you_met(tmp_path, monkeypatch):
    engine = _engine(tmp_path, monkeypatch)
    engine.tick()

    met = {name for name, _ in engine.history.people_met()}
    assert "ukso" not in met
    assert "Marzipan" in met


def test_session_only_history_is_wiped_when_vrchat_closes(tmp_path, monkeypatch):
    engine = _engine(tmp_path, monkeypatch, session_only=True)
    engine.tick()
    assert engine.history.recent_visits()

    engine._is_running = lambda: False
    engine.tick()

    assert engine.history.recent_visits() == []
    assert engine.history.people_met() == []


def test_persistent_history_survives_vrchat_closing(tmp_path, monkeypatch):
    engine = _engine(tmp_path, monkeypatch, session_only=False)
    engine.tick()

    engine._is_running = lambda: False
    engine.tick()

    assert engine.history.recent_visits()


def test_chatbox_tokens_include_media(tmp_path, monkeypatch):
    monkeypatch.setattr("vrcpresence.config.data_dir", lambda: tmp_path)
    monkeypatch.setattr(
        "vrcpresence.engine.now_playing",
        lambda: NowPlaying(artist="Artist", title="Song", player="spotify", playing=True),
    )
    engine = _engine(tmp_path, monkeypatch)
    engine.tick()

    tokens = engine.chatbox_tokens()
    assert tokens["song"] == "Song - Artist"
    assert tokens["artist"] == "Artist"
    assert tokens["world"] == "The Great Pug"


def test_media_off_leaves_song_empty(tmp_path, monkeypatch):
    engine = _engine(tmp_path, monkeypatch)
    engine.config.chatbox_media = False
    assert engine.chatbox_tokens()["song"] == ""


def test_now_playing_formatting():
    assert NowPlaying(artist="A", title="T").format() == "T - A"
    assert NowPlaying(title="T").format() == "T"
    assert NowPlaying().format() == ""
