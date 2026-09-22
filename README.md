# vrcpresence

[![CI](https://github.com/uksoKon/vrcpresence/actions/workflows/ci.yml/badge.svg)](https://github.com/uksoKon/vrcpresence/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-only-FCC624?logo=linux&logoColor=black)
![License](https://img.shields.io/badge/license-MIT-blue)

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
- **Chatbox status** - either a single rotating template, or an assembled
  line built from independent components (see below), each with its own
  VR/Desktop switch
- **Notifications** - desktop popup when someone joins or leaves
- **History** - local record of worlds visited, time spent and who you ran
  into. Session-scoped by default: wiped when VRChat closes, nothing kept
  between sessions, and you're never counted among people you ran into
- **Desktop theming** - reads colours, font and corner radius from
  `~/.config/serpantinum/settings.json` (or any tool that writes the same
  format, including matugen) and re-themes live when it changes

### Chatbox components

Inspired by [MagicChatBox](https://github.com/BoiHanny/vrcosc-magicchatbox)'s
approach of assembling one line from independent pieces, trimmed to VRChat's
144-character limit by dropping the lowest-priority piece first rather than
truncating mid-word:

| Component | Source |
| :-- | :-- |
| World & players | VRChat's own log |
| Now playing | MPRIS via `playerctl` - Spotify, browsers, VLC, anything |
| Synced lyrics | [LRCLIB](https://lrclib.net), no account |
| Time | System clock |
| Weather | [Open-Meteo](https://open-meteo.com), no account, coordinates you enter yourself |
| Component stats | CPU / GPU / RAM / temperature from `/proc` and `/sys` |
| Network | Live down/up rate |
| Window activity | Focused app, with a password-manager blocklist on by default and titles off by default |
| Personal status | Your own text |

Not included, with reasons: Soundpad and Voicemod are Windows-only apps;
tracker battery and VR performance need the OpenVR/SteamVR overlay API, not
available the same way under Proton; heart rate (Pulsoid), Spotify's API,
Twitch and TikTok all need paid or OAuth-gated accounts; IntelliChat is
AI-based and out of scope for this project on purpose.

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
