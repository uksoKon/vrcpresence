import builtins

from vrcpresence import openvr_source
from vrcpresence.openvr_source import (
    OpenVRReading,
    TrackedDevice,
    VRPerformance,
    format_battery,
    format_performance,
    read,
)


def test_reading_is_empty_by_default():
    assert OpenVRReading().is_empty


def test_reading_not_empty_with_devices():
    assert not OpenVRReading(devices=[TrackedDevice("hmd", 80.0)]).is_empty


def test_format_battery_skips_unknown_levels():
    devices = [
        TrackedDevice("hmd", 62.0),
        TrackedDevice("left", None),
        TrackedDevice("right", 88.0, charging=True),
    ]
    text = format_battery(devices)
    assert "hmd" in text and "62" in text
    assert "left" not in text
    assert "right" in text and "⚡" in text


def test_format_performance_hides_reprojection_when_low():
    assert format_performance(VRPerformance(fps=90.0, reprojection_ratio=0.01)) == "90fps"


def test_format_performance_warns_on_high_reprojection():
    text = format_performance(VRPerformance(fps=45.0, reprojection_ratio=0.4))
    assert "45fps" in text
    assert "reproj" in text


def test_format_performance_empty_without_fps():
    assert format_performance(VRPerformance()) == ""


def test_read_without_pyopenvr_installed_is_empty(monkeypatch):
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "openvr":
            raise ImportError("simulated: pyopenvr not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    assert read().is_empty


def test_read_without_steamvr_running_is_empty():
    # openvr IS installed in this environment (it's an optional dependency),
    # but no SteamVR/headset is running, so init() fails and this must
    # degrade to empty rather than raise.
    assert openvr_source.available()
    assert read().is_empty
