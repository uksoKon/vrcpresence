"""Tracker battery and VR performance via OpenVR.

SteamVR runs natively on Linux, and VRChat (even under Proton) talks to that
same native SteamVR instance over the OpenVR IPC pipe - so a native Linux
process can query it directly through `pyopenvr`, same as MagicChatbox does
on Windows. This is optional: without pyopenvr installed, or without SteamVR
running, every function here just returns nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrackedDevice:
    role: str
    battery_percent: float | None
    charging: bool = False


@dataclass(frozen=True)
class VRPerformance:
    fps: float | None = None
    dropped_frames: int | None = None
    reprojection_ratio: float | None = None


@dataclass(frozen=True)
class OpenVRReading:
    devices: list[TrackedDevice] = field(default_factory=list)
    performance: VRPerformance = field(default_factory=VRPerformance)

    @property
    def is_empty(self) -> bool:
        return not self.devices and self.performance.fps is None


def available() -> bool:
    try:
        import openvr  # noqa: F401
    except ImportError:
        return False
    return True


# ETrackedControllerRole: Invalid=0, LeftHand=1, RightHand=2.
_CONTROLLER_ROLE_NAMES = {1: "left", 2: "right"}


def read() -> OpenVRReading:
    """One-shot read. Initializing OpenVR is expensive, so callers should
    cache and call this on a slow interval, not every chatbox refresh.

    This has not been exercised against a real headset in development (no VR
    hardware available while building it) - unlike the rest of this project,
    the exact pyopenvr call surface here is unverified. Any mismatch degrades
    to an empty reading rather than crashing the poll loop.
    """
    try:
        import openvr
    except ImportError:
        return OpenVRReading()

    try:
        vr_system = openvr.init(openvr.VRApplication_Background)
        try:
            devices = _read_devices(openvr, vr_system)
            performance = _read_performance(openvr, vr_system)
        finally:
            openvr.shutdown()
    except Exception:  # noqa: BLE001 - unverified API surface, must not crash the poll loop
        return OpenVRReading()

    return OpenVRReading(devices=devices, performance=performance)


def _device_role(openvr, vr_system, index: int, device_class: int) -> str:
    if device_class == openvr.TrackedDeviceClass_HMD:
        return "hmd"
    if device_class == openvr.TrackedDeviceClass_Controller:
        role = vr_system.getControllerRoleForTrackedDeviceIndex(index)
        return _CONTROLLER_ROLE_NAMES.get(role, "controller")
    if device_class == openvr.TrackedDeviceClass_GenericTracker:
        return "tracker"
    return "device"


def _read_devices(openvr, vr_system) -> list[TrackedDevice]:
    devices: list[TrackedDevice] = []
    for index in range(openvr.k_unMaxTrackedDeviceCount):
        device_class = vr_system.getTrackedDeviceClass(index)
        if device_class == openvr.TrackedDeviceClass_Invalid:
            continue
        if not vr_system.isTrackedDeviceConnected(index):
            continue

        try:
            battery = vr_system.getFloatTrackedDeviceProperty(
                index, openvr.Prop_DeviceBatteryPercentage_Float
            )
        except openvr.OpenVRError:
            battery = None

        try:
            charging = vr_system.getBoolTrackedDeviceProperty(
                index, openvr.Prop_DeviceIsCharging_Bool
            )
        except openvr.OpenVRError:
            charging = False

        devices.append(
            TrackedDevice(
                role=_device_role(openvr, vr_system, index, device_class),
                battery_percent=round(battery * 100) if battery is not None else None,
                charging=bool(charging),
            )
        )

    return devices


def _read_performance(openvr, vr_system) -> VRPerformance:
    import ctypes

    try:
        timing = openvr.Compositor_FrameTiming()
        timing.m_nSize = ctypes.sizeof(timing)
        compositor = openvr.VRCompositor()
        if compositor is None or not compositor.getFrameTiming(timing):
            return VRPerformance()
    except (openvr.OpenVRError, AttributeError, ctypes.ArgumentError):
        return VRPerformance()

    frame_interval = getattr(timing, "m_flSystemTimeInSeconds", None)
    dropped = getattr(timing, "m_nNumDroppedFrames", None)
    reprojected = getattr(timing, "m_nNumReprojectedFrames", None)

    fps = 1.0 / frame_interval if frame_interval else None
    ratio = None
    if dropped is not None and reprojected is not None:
        total = dropped + reprojected + 1
        ratio = reprojected / total

    return VRPerformance(fps=fps, dropped_frames=dropped, reprojection_ratio=ratio)


def format_battery(devices: list[TrackedDevice]) -> str:
    parts = []
    for device in devices:
        if device.battery_percent is None:
            continue
        icon = "⚡" if device.charging else "\U0001f50b"
        parts.append(f"{device.role} {icon}{device.battery_percent:.0f}%")
    return " ".join(parts)


def format_performance(perf: VRPerformance) -> str:
    if perf.fps is None:
        return ""
    text = f"{perf.fps:.0f}fps"
    if perf.reprojection_ratio is not None and perf.reprojection_ratio > 0.05:
        text += f" ⚠{perf.reprojection_ratio * 100:.0f}%reproj"
    return text
