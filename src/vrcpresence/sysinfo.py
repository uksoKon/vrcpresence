"""Local hardware readings for the chatbox: CPU, memory, GPU, network.

Everything here comes from /proc and /sys, so there's no dependency and
nothing leaves the machine. Rate-based values need two samples, so the
collectors hold the previous reading.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

PROC_STAT = Path("/proc/stat")
PROC_MEMINFO = Path("/proc/meminfo")
PROC_NET_DEV = Path("/proc/net/dev")
HWMON = Path("/sys/class/hwmon")

SKIP_INTERFACES = ("lo", "docker", "veth", "br-", "virbr", "tun", "tap")


def _read(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""


class CpuUsage:
    """Percentage busy since the previous call."""

    def __init__(self) -> None:
        self._previous: tuple[int, int] | None = None

    def read(self) -> float | None:
        line = _read(PROC_STAT).split("\n", 1)[0]
        if not line.startswith("cpu "):
            return None

        values = [int(v) for v in line.split()[1:] if v.isdigit()]
        if len(values) < 4:
            return None

        idle = values[3] + (values[4] if len(values) > 4 else 0)
        total = sum(values)

        previous = self._previous
        self._previous = (idle, total)
        if previous is None:
            return None

        idle_delta = idle - previous[0]
        total_delta = total - previous[1]
        if total_delta <= 0:
            return None
        return max(0.0, min(100.0, (1 - idle_delta / total_delta) * 100))


def memory_usage() -> float | None:
    """Percentage of RAM in use."""
    values: dict[str, int] = {}
    for line in _read(PROC_MEMINFO).splitlines():
        key, _, rest = line.partition(":")
        parts = rest.split()
        if parts and parts[0].isdigit():
            values[key] = int(parts[0])

    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if not total or available is None:
        return None
    return max(0.0, min(100.0, (1 - available / total) * 100))


def cpu_temperature() -> float | None:
    """Package temperature in celsius, from whichever hwmon exposes it."""
    preferred = ("k10temp", "coretemp", "zenpower", "acpitz")
    fallback: float | None = None

    for entry in sorted(HWMON.glob("hwmon*")) if HWMON.is_dir() else []:
        name = _read(entry / "name").strip()
        for sensor in sorted(entry.glob("temp*_input")):
            raw = _read(sensor).strip()
            if not raw.isdigit():
                continue
            celsius = int(raw) / 1000
            if not 0 < celsius < 150:
                continue
            if name in preferred:
                return celsius
            if fallback is None:
                fallback = celsius

    return fallback


@dataclass(frozen=True)
class GpuReading:
    name: str = ""
    usage: float | None = None
    temperature: float | None = None


def gpu_reading() -> GpuReading:
    """AMD/Intel GPU via /sys; NVIDIA needs its own tool and is skipped."""
    for card in sorted(Path("/sys/class/drm").glob("card[0-9]")) if Path(
        "/sys/class/drm"
    ).is_dir() else []:
        device = card / "device"
        busy = _read(device / "gpu_busy_percent").strip()
        usage = float(busy) if busy.isdigit() else None

        temperature = None
        for hwmon in sorted((device / "hwmon").glob("hwmon*")) if (
            device / "hwmon"
        ).is_dir() else []:
            raw = _read(hwmon / "temp1_input").strip()
            if raw.isdigit():
                temperature = int(raw) / 1000
                break

        if usage is not None or temperature is not None:
            return GpuReading(name=card.name, usage=usage, temperature=temperature)

    return GpuReading()


class NetworkRate:
    """Download and upload in megabits per second."""

    def __init__(self) -> None:
        self._previous: tuple[float, int, int] | None = None

    def read(self) -> tuple[float, float] | None:
        received = 0
        sent = 0
        for line in _read(PROC_NET_DEV).splitlines()[2:]:
            name, _, rest = line.partition(":")
            name = name.strip()
            if not name or name.startswith(SKIP_INTERFACES):
                continue
            fields = rest.split()
            if len(fields) < 9:
                continue
            received += int(fields[0])
            sent += int(fields[8])

        now = time.monotonic()
        previous = self._previous
        self._previous = (now, received, sent)
        if previous is None:
            return None

        elapsed = now - previous[0]
        if elapsed <= 0:
            return None

        down = (received - previous[1]) * 8 / elapsed / 1_000_000
        up = (sent - previous[2]) * 8 / elapsed / 1_000_000
        return (max(0.0, down), max(0.0, up))
