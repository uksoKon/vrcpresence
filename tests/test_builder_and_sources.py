from vrcpresence.builder import Component, build_line
from vrcpresence.components import network_text, system_text, world_text
from vrcpresence.lyrics import TimedLine, line_at, parse_lrc
from vrcpresence.osc_client import MAX_CHATBOX_CHARS
from vrcpresence.state import SessionState
from vrcpresence.sysinfo import GpuReading
from vrcpresence.weather import Weather
from vrcpresence.window_activity import ActiveWindow, describe


def test_build_line_joins_in_declared_order():
    result = build_line(
        [
            Component("a", "first", priority=10),
            Component("b", "second", priority=90),
        ]
    )
    assert result.text == "first | second"
    assert result.used == ["a", "b"]


def test_build_line_skips_empty_components():
    result = build_line([Component("a", "here"), Component("b", "   ")])
    assert result.text == "here"


def test_build_line_drops_lowest_priority_when_too_long():
    """The point of the whole thing: never truncate the song mid-word."""
    keep = Component("keep", "K" * 100, priority=90)
    drop = Component("drop", "D" * 100, priority=10)

    result = build_line([keep, drop])
    assert result.text == "K" * 100
    assert result.used == ["keep"]
    assert "drop" in result.dropped
    assert len(result.text) <= MAX_CHATBOX_CHARS


def test_build_line_drops_repeatedly_until_it_fits():
    components = [Component(f"c{i}", "X" * 50, priority=i) for i in range(5)]
    result = build_line(components)
    assert len(result.text) <= MAX_CHATBOX_CHARS
    assert result.used  # something survived
    assert result.dropped


def test_build_line_respects_vr_only_components():
    components = [
        Component("vr", "headset", in_vr=True, on_desktop=False),
        Component("desk", "monitor", in_vr=False, on_desktop=True),
    ]
    assert build_line(components, in_vr=True).text == "headset"
    assert build_line(components, in_vr=False).text == "monitor"


def test_build_line_unknown_mode_keeps_everything():
    components = [
        Component("vr", "headset", in_vr=True, on_desktop=False),
        Component("desk", "monitor", in_vr=False, on_desktop=True),
    ]
    assert build_line(components, in_vr=None).text == "headset | monitor"


def test_world_text_variants():
    state = SessionState(world_id="wrld_a", instance_id="1", world_name="The Great Pug")
    state.players = ["a", "b"]
    assert world_text(state, running=True) == "The Great Pug (2)"

    state.world_capacity = 40
    assert world_text(state, running=True) == "The Great Pug (2/40)"

    assert world_text(state, running=False) == ""
    assert world_text(SessionState(), running=True) == "loading"


def test_system_text_omits_unavailable_readings():
    assert system_text(42.0, 60.0, GpuReading(), None) == "CPU 42% RAM 60%"
    assert system_text(None, None, GpuReading(usage=77.0), 55.0) == "55°C GPU 77%"
    assert system_text(None, None, GpuReading(), None) == ""


def test_network_text():
    assert network_text((12.4, 3.2)) == "↓12 ↑3 Mbps"
    assert network_text(None) == ""


def test_weather_format():
    assert Weather(temperature=14.2, code=61).format() == "☔ 14°C"
    assert Weather().format() == ""


def test_window_describe_hides_titles_by_default():
    window = ActiveWindow(app="Blender", title="secret_project.blend")
    assert describe(window) == "Blender"
    assert describe(window, show_title=True) == "Blender: secret_project.blend"


def test_window_describe_blocks_sensitive_apps():
    assert describe(ActiveWindow(app="KeePassXC", title="vault")) == ""
    assert describe(ActiveWindow(app="firefox", title="1Password")) == ""


def test_parse_lrc_and_pick_current_line():
    body = "[00:12.50] first line\n[00:20.00] second line\n[bad]\n[00:30.00]   \n"
    lines = parse_lrc(body)
    assert lines == [TimedLine(12.5, "first line"), TimedLine(20.0, "second line")]

    assert line_at(lines, 0) == ""
    assert line_at(lines, 15) == "first line"
    assert line_at(lines, 25) == "second line"
    assert line_at(lines, 9999) == "second line"
