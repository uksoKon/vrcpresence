from pathlib import Path

from vrcpresence.discord_presence import build_presence, launch_url
from vrcpresence.log_watcher import parse_lines
from vrcpresence.osc_client import MAX_CHATBOX_CHARS, format_chatbox_text
from vrcpresence.state import SessionState

FIXTURES = Path(__file__).parent / "fixtures"


def state_from_fixture() -> SessionState:
    state = SessionState()
    with (FIXTURES / "session.log").open() as f:
        state.apply_all(list(parse_lines(f)))
    return state


def test_state_tracks_latest_world():
    state = state_from_fixture()
    assert state.world_name == "The Great Pug"
    assert state.world_id == "wrld_ba913a96-fac4-4048-a062-9aa5db092812"
    assert state.in_world


def test_state_resets_players_between_worlds():
    """Players from the previous instance must not leak into the next one."""
    state = state_from_fixture()
    assert sorted(state.players) == ["Marzipan", "ukso"]


def test_state_tracks_desktop_mode():
    assert state_from_fixture().in_vr is False


def test_state_left_room_clears_everything():
    from vrcpresence.events import LeftRoom

    state = state_from_fixture()
    state.apply(LeftRoom())
    assert not state.in_world
    assert state.players == []
    assert state.world_name is None


def test_presence_when_idle():
    payload = build_presence(SessionState())
    assert payload["details"] == "Not in a world"
    assert "join" not in payload


def test_presence_includes_world_image_and_party():
    state = state_from_fixture()
    state.world_image_url = "https://api.vrchat.cloud/image.png"
    state.world_capacity = 40

    payload = build_presence(state)
    assert payload["details"] == "The Great Pug"
    assert payload["large_image"] == "https://api.vrchat.cloud/image.png"
    assert payload["party_size"] == [2, 40]
    assert payload["small_text"] == "Desktop"


def test_presence_join_can_be_disabled():
    state = state_from_fixture()
    assert "join" in build_presence(state, allow_join=True)
    assert "join" not in build_presence(state, allow_join=False)


def test_presence_hides_players_when_asked():
    state = state_from_fixture()
    payload = build_presence(state, show_players=False)
    assert "state" not in payload
    assert "party_size" not in payload


def test_launch_url_round_trip():
    url = launch_url("wrld_abc:12345~public")
    assert "worldId=wrld_abc" in url
    assert "instanceId=12345~public" in url


def test_chatbox_template_tokens():
    text = format_chatbox_text("{world} - {players} here", {"world": "Pug", "players": "3"})
    assert text == "Pug - 3 here"


def test_chatbox_unknown_token_is_left_alone():
    assert format_chatbox_text("{nope}", {"world": "x"}) == "{nope}"


def test_chatbox_text_is_clamped():
    assert len(format_chatbox_text("x" * 500, {})) == MAX_CHATBOX_CHARS
