from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Config, data_dir
from .events import HeadsetMode, PlayerJoin, PlayerLeave, WorldJoin, WorldName
from .log_watcher import XR_HINT, find_latest_log, find_log_dir, parse_line
from .state import SessionState


def cmd_calibrate(args: argparse.Namespace) -> int:
    """Replay a log file and report what the parser understood.

    VRChat's log format is undocumented and shifts between updates, so every
    tool built on it eventually parses nothing and silently shows an empty
    status. This makes that failure visible in one command.
    """
    path = Path(args.log) if args.log else _discover_log()
    if path is None:
        print("error: no VRChat log found; pass one explicitly", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return 2

    print(f"Reading {path}\n")

    counts = {"world_join": 0, "world_name": 0, "player_join": 0, "player_leave": 0, "mode": 0}
    state = SessionState()
    total_lines = 0
    xr_lines: list[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            total_lines += 1
            if len(xr_lines) < 8 and XR_HINT.search(line):
                xr_lines.append(line.strip())
            event = parse_line(line)
            if event is None:
                continue
            state.apply(event)

            if isinstance(event, WorldJoin):
                counts["world_join"] += 1
                print(f"  world   {event.world_id}:{event.instance_id}")
            elif isinstance(event, WorldName):
                counts["world_name"] += 1
                print(f"  name    {event.name}")
            elif isinstance(event, PlayerJoin):
                counts["player_join"] += 1
                if args.verbose:
                    print(f"  join    {event.display_name}")
            elif isinstance(event, PlayerLeave):
                counts["player_leave"] += 1
                if args.verbose:
                    print(f"  leave   {event.display_name}")
            elif isinstance(event, HeadsetMode):
                counts["mode"] += 1
                if counts["mode"] == 1 or args.verbose:
                    print(f"  mode    {'VR' if event.in_vr else 'Desktop'}")

    print(f"\n{total_lines} lines read")
    for key, value in counts.items():
        print(f"  {key:<13} {value}")

    print("\nFinal state:")
    print(f"  world    {state.world_name or state.world_id or '(none)'}")
    print(f"  players  {state.player_count}")
    print(f"  mode     {'VR' if state.in_vr else 'Desktop' if state.in_vr is False else '(unknown)'}")

    if state.in_vr is None and xr_lines:
        print("\nMode was not detected. These XR lines are what your log actually says -")
        print("the pattern to update is log_watcher.PATTERNS['vr_mode' / 'desktop_mode']:")
        for line in xr_lines:
            print(f"  {line}")

    if counts["world_join"] == 0 and counts["player_join"] == 0:
        print(
            "\nNothing matched. VRChat's log format has probably changed - "
            "the patterns to update are in log_watcher.PATTERNS.",
            file=sys.stderr,
        )
        return 1
    return 0


def _discover_log() -> Path | None:
    log_dir = find_log_dir()
    return find_latest_log(log_dir) if log_dir else None


def cmd_where(args: argparse.Namespace) -> int:
    """Report where vrcpresence thinks VRChat keeps its logs."""
    log_dir = find_log_dir()
    if log_dir is None:
        print("No VRChat log directory found.")
        print("Checked Steam libraries for the VRChat Proton prefix (appid 438100).")
        return 1
    print(f"log directory: {log_dir}")
    latest = find_latest_log(log_dir)
    print(f"latest log:    {latest if latest else '(none)'}")
    print(f"history db:    {data_dir() / 'history.db'}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Headless mode: presence and chatbox with no GUI."""
    from .engine import Engine

    config = Config.load()
    if args.chatbox:
        config.chatbox_enabled = True

    engine = Engine(config)
    print("vrcpresence running (ctrl-c to stop)")
    engine.run()
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    from .history import History

    history = History(data_dir() / "history.db")
    visits = history.recent_visits(limit=args.limit)
    if not visits:
        print("No visits recorded yet.")
        return 0

    for visit in visits:
        when = visit.joined_at.astimezone().strftime("%Y-%m-%d %H:%M")
        duration = visit.duration_seconds
        length = f"{duration / 60:.0f}m" if duration else "ongoing"
        name = visit.world_name or visit.world_id
        print(f"{when}  {length:>8}  peak {visit.peak_players:>2}  {name}")

    totals = history.totals()
    hours = totals["seconds"] / 3600
    print(
        f"\n{totals['visits']} visits, {totals['unique_worlds']} worlds, "
        f"{hours:.1f}h, {totals['people_met']} people met"
    )
    history.close()
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    from .gui.app import run_gui

    return run_gui()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vrcpresence",
        description="VRChat status, Discord Rich Presence and chatbox for Linux.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_gui = sub.add_parser("gui", help="launch the interface (default)")
    p_gui.set_defaults(func=cmd_gui)

    p_run = sub.add_parser("run", help="run headless, no window")
    p_run.add_argument("--chatbox", action="store_true", help="also push status to the chatbox")
    p_run.set_defaults(func=cmd_run)

    p_cal = sub.add_parser("calibrate", help="replay a log and show what the parser understood")
    p_cal.add_argument("log", nargs="?", help="log file (defaults to the newest one found)")
    p_cal.add_argument("-v", "--verbose", action="store_true", help="list every player event")
    p_cal.set_defaults(func=cmd_calibrate)

    p_where = sub.add_parser("where", help="show detected VRChat log and data paths")
    p_where.set_defaults(func=cmd_where)

    p_hist = sub.add_parser("history", help="list recent worlds you've visited")
    p_hist.add_argument("-n", "--limit", type=int, default=20)
    p_hist.set_defaults(func=cmd_history)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
