# vrcpresence

VRChat status, Discord Rich Presence and chatbox control for Linux.

Shows the world you're in on your Discord profile - with the world's own
thumbnail, a live headcount, a VR/Desktop badge and a Join button friends can
click to drop into your instance. Plus a rotating chatbox status, desktop
notifications when people come and go, and a private local record of every
world you've visited.

Built for Linux and Proton. No Wine layer, no Windows build.

## Why the world info actually works here

VRChat's OSC API cannot tell you what world you're in, who is with you, or
whether you're in VR - it only exposes avatar parameters, input and the
chatbox. Tools that try to read world data over OSC sit there listening for
messages VRChat never sends, which is why they show an empty status forever.

vrcpresence reads VRChat's own log file instead, which is where that
information actually lives. The patterns are verified against a real log, and
`vrcpresence calibrate` re-verifies them on demand.

## Install

```
pip install -e ".[api]"
```

The `api` extra pulls in `vrchatapi`, used only to turn a world ID into a
thumbnail image. Everything else - world name, players, VR/Desktop, chatbox,
presence - works with no account and no credentials.

## Usage

```
vrcpresence gui        # the interface
vrcpresence run        # headless, no window
vrcpresence calibrate  # check the log parser against your own log
vrcpresence where      # show the detected VRChat log and data paths
vrcpresence history    # worlds you've visited
```

### calibrate

VRChat's log format is undocumented and changes between updates. When it
does, every tool built on it silently parses nothing and shows a blank
status. `calibrate` replays your newest log and prints exactly what it
understood:

```
$ vrcpresence calibrate

  mode    Desktop
  world   wrld_00000000-0000-0000-0000-000000000000:12345~public
  name    The Great Pug

1572 lines read
  world_join    1
  world_name    1
  player_join   1
  player_leave  0
  mode          5
```

If nothing matches, it says so and points at the patterns to fix. If the
VR/Desktop mode can't be determined, it prints the XR lines your log actually
contains so the pattern can be corrected in one line.

## Features

- **Discord Rich Presence** - world name, world thumbnail, live headcount as a
  party size, VR or Desktop badge, elapsed time
- **Join button** - friends click your presence and land in your instance
- **Private mode** - one switch blanks your presence without closing the app
- **Chatbox status** - rotating templates with `{world}`, `{players}`,
  `{capacity}` and `{mode}` tokens
- **Notifications** - desktop popup when someone joins or leaves
- **History** - local SQLite record of worlds visited, time spent and who you
  ran into, queryable from the History tab or `vrcpresence history`

## How it finds things

- Scans every Steam library on the machine, including extra drives, for the
  VRChat Proton prefix (appid 438100)
- Follows log rotation: VRChat opens a new log file each launch, and the
  watcher switches to it automatically instead of going silent
- Discord being closed is not an error - the presence client reconnects
  quietly when Discord shows up

## Known gap

Desktop detection is verified against a real log (the `--no-vr` launch flag
and VRChat's XR stack failing to initialize). **VR detection is not yet
confirmed against a real VR session** - if you play in VR, run
`vrcpresence calibrate` and check whether the reported mode says VR. If it
says unknown, the command prints the lines needed to fix it.

## Development

```
pip install -e ".[dev,api]"
ruff check .
pytest
```

The test suite includes a QML smoke test that captures Qt's own warnings and
fails on any binding error, so a broken interface can't pass as working.

## License

MIT
