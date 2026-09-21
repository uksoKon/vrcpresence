from pathlib import Path

from vrcpresence.events import HeadsetMode, LeftRoom, PlayerJoin, PlayerLeave, WorldJoin, WorldName
from vrcpresence.log_watcher import LogWatcher, find_latest_log, parse_line

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_world_join():
    line = "2026.09.21 18:02:31 Log        -  [Behaviour] Joining wrld_4432ea9b-729c-46e3-8eaf-846aa0a37fdd:47281~region(use)"
    event = parse_line(line)
    assert isinstance(event, WorldJoin)
    assert event.world_id == "wrld_4432ea9b-729c-46e3-8eaf-846aa0a37fdd"
    assert event.instance_id == "47281~region(use)"


def test_parse_world_name():
    event = parse_line("... [Behaviour] Joining or Creating Room: The Black Cat")
    assert isinstance(event, WorldName)
    assert event.name == "The Black Cat"


def test_parse_player_join_with_user_id():
    event = parse_line(
        "... [Behaviour] OnPlayerJoined ukso (usr_8a3d1c77-1111-4a4c-9d0e-0b9a77aa1234)"
    )
    assert isinstance(event, PlayerJoin)
    assert event.display_name == "ukso"
    assert event.user_id == "usr_8a3d1c77-1111-4a4c-9d0e-0b9a77aa1234"


def test_parse_player_join_without_user_id():
    event = parse_line("... [Behaviour] OnPlayerJoined Neon Fox")
    assert isinstance(event, PlayerJoin)
    assert event.display_name == "Neon Fox"
    assert event.user_id is None


def test_parse_player_leave():
    event = parse_line("... [Behaviour] OnPlayerLeft Neon Fox")
    assert isinstance(event, PlayerLeave)
    assert event.display_name == "Neon Fox"


def test_parse_left_room():
    assert isinstance(parse_line("... [Behaviour] OnLeftRoom"), LeftRoom)


def test_parse_desktop_mode_from_launch_flag():
    event = parse_line("2026.09.21 15:06:01 Debug      -  Arg: --no-vr")
    assert isinstance(event, HeadsetMode)
    assert event.in_vr is False


def test_parse_desktop_mode_from_failed_openvr():
    """Verbatim from a real log: no headset means OpenVR never initializes."""
    line = (
        "2026.09.21 15:06:02 Error      -  <b>[OpenVR]</b> Could not initialize OpenVR. "
        "Error code: Init_InterfaceNotFound"
    )
    event = parse_line(line)
    assert isinstance(event, HeadsetMode)
    assert event.in_vr is False


def test_parse_desktop_mode_from_failed_steamvr():
    line = (
        "2026.09.21 15:06:02 Warning    -  <b>[SteamVR]</b> Initialization failed. "
        "Please verify that you have SteamVR installed"
    )
    event = parse_line(line)
    assert isinstance(event, HeadsetMode)
    assert event.in_vr is False


def test_parse_ignores_noise():
    assert parse_line("2026.09.21 18:02:14 Log - [Behaviour] Initializing VRChat") is None


def test_watcher_reads_incrementally(tmp_path):
    log = tmp_path / "output_log_00-00-00.txt"
    log.write_text("... [Behaviour] Joining wrld_aaa:1\n")

    watcher = LogWatcher(log_dir=tmp_path)
    first = watcher.poll()
    assert len(first) == 1

    assert watcher.poll() == []

    with log.open("a") as f:
        f.write("... [Behaviour] OnPlayerJoined Kettle\n")

    second = watcher.poll()
    assert len(second) == 1
    assert isinstance(second[0], PlayerJoin)


def test_watcher_follows_log_rotation(tmp_path):
    """VRChat opens a fresh log every launch; the watcher must follow it."""
    import os
    import time

    old = tmp_path / "output_log_01-00-00.txt"
    old.write_text("... [Behaviour] OnPlayerJoined Old\n")

    watcher = LogWatcher(log_dir=tmp_path)
    assert len(watcher.poll()) == 1
    assert watcher.current_log == old

    time.sleep(0.01)
    new = tmp_path / "output_log_02-00-00.txt"
    new.write_text("... [Behaviour] OnPlayerJoined New\n")
    os.utime(new, (time.time() + 10, time.time() + 10))

    events = watcher.poll()
    assert watcher.current_log == new
    assert [e.display_name for e in events] == ["New"]


def test_watcher_handles_truncation(tmp_path):
    log = tmp_path / "output_log_00-00-00.txt"
    log.write_text("... [Behaviour] OnPlayerJoined A\n... [Behaviour] OnPlayerJoined B\n")

    watcher = LogWatcher(log_dir=tmp_path)
    assert len(watcher.poll()) == 2

    log.write_text("... [Behaviour] OnPlayerJoined C\n")
    events = watcher.poll()
    assert [e.display_name for e in events] == ["C"]


def test_watcher_without_log_dir_is_quiet(tmp_path):
    assert LogWatcher(log_dir=tmp_path / "nope").poll() == []


def test_find_latest_log_picks_newest(tmp_path):
    import os
    import time

    first = tmp_path / "output_log_01.txt"
    second = tmp_path / "output_log_02.txt"
    first.write_text("a")
    second.write_text("b")
    os.utime(second, (time.time() + 60, time.time() + 60))

    assert find_latest_log(tmp_path) == second
