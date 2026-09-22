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

For the optional social/hardware integrations below:

```
pip install -e ".[integrations]"   # everything, or pick one:
pip install -e ".[heartrate]"      # Pulsoid heart rate
pip install -e ".[tiktok]"         # TikTok Live
pip install -e ".[discord-voice]"  # Discord voice channel presence
pip install -e ".[vr]"             # OpenVR tracker battery / VR performance
```

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
truncating mid-word. Every component has its own VR/Desktop visibility
switch, so your rig stats can show at your desk and your music in the
headset, automatically.

| Component | Source | Needs |
| :-- | :-- | :-- |
| World & players | VRChat's own log | nothing |
| Now playing | MPRIS via `playerctl` - Spotify, browsers, VLC, anything | nothing |
| Synced lyrics | [LRCLIB](https://lrclib.net) | nothing |
| Time | System clock | nothing |
| Weather | [Open-Meteo](https://open-meteo.com) | coordinates you enter |
| Component stats | CPU / GPU / RAM / temperature from `/proc` and `/sys` | nothing |
| Network | Live down/up rate | nothing |
| Window activity | Focused app - password managers blocked by default, titles off by default | nothing |
| Personal status | Your own text | nothing |
| Tracker battery / VR performance | SteamVR via `pyopenvr` (runs natively on Linux) | `pip install .[vr]` |
| Heart rate | [Pulsoid](https://pulsoid.net) WebSocket | your own access token |
| Spotify | Liked/explicit/shuffle/repeat/device/volume, replaces generic Now Playing | free Spotify app (Client ID only, PKCE - no secret) |
| Twitch | Live status, category, viewers, followers | free Twitch app (Client ID + Secret, read-only, no viewer login) |
| TikTok Live | Viewer count, follows, gifts | your public username, `pip install .[tiktok]` |
| Discord voice | Who's in your voice channel | a bot you create, `pip install .[discord-voice]` (not a self-bot) |
| IntelliChat | AI spelling fix + smart shortening | **off by default** - your own OpenAI-compatible API key |

**Not included:** Soundpad and Voicemod are Windows-only apps with no Linux
client at all - there's nothing here to connect to.

IntelliChat is the one AI-based piece, included because it was explicitly
asked for after being flagged as inconsistent with the rest of this project's
no-AI stance - it's off by default, clearly labeled in the UI, and inert
without an API key you provide yourself.

## How it finds things

- Scans every Steam library on the machine, including extra drives, for the
  VRChat Proton prefix (appid 438100)
- Follows log rotation: VRChat opens a new log file each launch, and the
  watcher switches to it automatically instead of going silent
- Discord being closed is not an error - the presence client reconnects
  quietly when Discord shows up

## Known gaps

Desktop detection is verified against a real log (the `--no-vr` launch flag
and VRChat's XR stack failing to initialize). **VR detection is not yet
confirmed against a real VR session** - if you play in VR, run
`vrcpresence calibrate` and check whether the reported mode says VR. If it
says unknown, the command prints the lines needed to fix it.

The tracker battery / VR performance integration was built and checked
against the real `pyopenvr` package (correct imports, correct constant and
method names) but not against an actual headset session, since none was
available while building it - if it comes back empty while SteamVR is
genuinely running, that's a bug, please report it. TikTok Live and Discord
voice were checked the same way, against the real installed packages'
actual event and field names rather than assumed ones.

## Development

```
pip install -e ".[dev,api,integrations]"
ruff check .
pytest
```

The test suite includes a QML smoke test that captures Qt's own warnings and
fails on any binding error, so a broken interface can't pass as working.

## License

MIT
