"""Assembles one chatbox line out of the enabled components.

VRChat allows 144 characters. Rather than truncating mid-word when the line
is too long, components are dropped whole, lowest priority first, so the
thing you care about most survives. Each component also declares whether it
should appear in VR, on desktop, or both - your rig stats at your desk, your
music in the headset.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .osc_client import MAX_CHATBOX_CHARS

SEPARATOR = " | "


@dataclass(frozen=True)
class Component:
    """One piece of the line."""

    key: str
    text: str
    priority: int = 50
    in_vr: bool = True
    on_desktop: bool = True

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


@dataclass
class BuildResult:
    text: str
    used: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)


def build_line(
    components: list[Component],
    *,
    in_vr: bool | None = None,
    separator: str = SEPARATOR,
    limit: int = MAX_CHATBOX_CHARS,
) -> BuildResult:
    """Join what fits, dropping the least important pieces first.

    in_vr=None means the headset mode is unknown, in which case no component
    is filtered out for it.
    """
    visible = [
        c
        for c in components
        if not c.is_empty and (in_vr is None or (c.in_vr if in_vr else c.on_desktop))
    ]

    dropped = [c.key for c in components if c not in visible and not c.is_empty]
    kept = sorted(visible, key=lambda c: (-c.priority, c.key))

    while kept:
        ordered = [c for c in components if c in kept]
        text = separator.join(c.text.strip() for c in ordered)
        if len(text) <= limit:
            return BuildResult(text=text, used=[c.key for c in ordered], dropped=dropped)
        dropped.append(kept[-1].key)
        kept = kept[:-1]

    return BuildResult(text="", used=[], dropped=dropped)
