import VrcPresence
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Flickable {
    contentHeight: column.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: ScrollBar {}

    function onCount(keys) {
        var n = 0;
        for (var i = 0; i < keys.length; i++) {
            if (Bridge.options[keys[i]] === true) n++;
        }
        return n + " on";
    }

    ColumnLayout {
        id: column
        width: parent.width
        spacing: Theme.gapTight

        Text {
            Layout.fillWidth: true
            Layout.bottomMargin: Theme.gapTight
            text: "Component mode builds the chatbox line from whatever's switched on below, "
                + "instead of a single fixed template. Turn it on in Chatbox → Send to chatbox."
            color: Theme.textFaint
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontMicro
            wrapMode: Text.WordWrap
        }

        // You --------------------------------------------------------------------

        CollapsibleSection {
            title: "You"
            subtitle: onCount(["show_world", "show_time", "show_weather", "show_lyrics", "show_window", "show_status"])
            open: true

            OptionSwitch {
                Layout.fillWidth: true
                icon: "◉"
                key: "show_world"
                label: "World"
                hint: "Where you are and the headcount"
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "◴"
                key: "show_time"
                label: "Time"
                hint: "Your local time - the most-asked question in any instance"
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "☁"
                key: "show_weather"
                label: "Weather"
                hint: "Needs coordinates below - Open-Meteo, no account"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                spacing: Theme.gapTight
                visible: Bridge.options.show_weather === true

                TextInput {
                    Layout.fillWidth: true
                    label: "Latitude"
                    placeholder: "51.5074"
                    value: Bridge.options.weather_latitude !== null
                        && Bridge.options.weather_latitude !== undefined
                        ? String(Bridge.options.weather_latitude) : ""
                    onCommitted: (v) => Bridge.setNumberOption("weather_latitude", v)
                }

                TextInput {
                    Layout.fillWidth: true
                    label: "Longitude"
                    placeholder: "-0.1278"
                    value: Bridge.options.weather_longitude !== null
                        && Bridge.options.weather_longitude !== undefined
                        ? String(Bridge.options.weather_longitude) : ""
                    onCommitted: (v) => Bridge.setNumberOption("weather_longitude", v)
                }
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "♪"
                key: "show_lyrics"
                label: "Synced lyrics"
                hint: "Current line as it's sung, from LRCLIB - needs Now Playing on"
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "■"
                key: "show_window"
                label: "Window activity"
                hint: "The app you're focused on. Blocks password managers automatically."
            }

            OptionSwitch {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                icon: "“"
                key: "window_titles"
                label: "Include window titles"
                hint: "Off shows just the app name - titles can contain document/video names"
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "●"
                key: "show_status"
                label: "Personal status"
                hint: "Your own message"
            }

            TextInput {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                visible: Bridge.options.show_status === true
                label: "Status text"
                placeholder: "back in 5"
                value: Bridge.options.personal_status || ""
                onCommitted: (v) => Bridge.setTextOption("personal_status", v)
            }
        }

        // Hardware -----------------------------------------------------------------

        CollapsibleSection {
            title: "Hardware"
            subtitle: onCount(["show_system", "show_network"])

            OptionSwitch {
                Layout.fillWidth: true
                icon: "⚙"
                key: "show_system"
                label: "Component stats"
                hint: "CPU, GPU, RAM, temperature - from /proc and /sys, no extra install"
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "↕"
                key: "show_network"
                label: "Network"
                hint: "Live download / upload rate"
            }
        }

        // VR -------------------------------------------------------------------------

        CollapsibleSection {
            title: "VR"
            subtitle: Bridge.openvrAvailable
                ? onCount(["show_tracker_battery", "show_vr_performance"])
                : "needs pyopenvr"

            Text {
                Layout.fillWidth: true
                visible: !Bridge.openvrAvailable
                wrapMode: Text.WordWrap
                text: "pip install \"vrcpresence[vr]\" - reads SteamVR, which runs natively on "
                    + "Linux. Unverified against real hardware while building this; if it comes "
                    + "back empty with SteamVR actually running, that's a bug to report."
                color: Theme.warn
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontMicro
                lineHeight: 1.3
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "◑"
                key: "show_tracker_battery"
                label: "Tracker battery"
                hint: "Headset, controllers, full-body trackers - before one dies mid-session"
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "⚡"
                key: "show_vr_performance"
                label: "VR performance"
                hint: "Frame rate and reprojection - quiet until something goes wrong"
            }
        }

        // Social & streaming -----------------------------------------------------------

        CollapsibleSection {
            title: "Social & streaming"
            subtitle: onCount(["show_heart_rate", "show_spotify", "show_twitch", "show_tiktok", "show_discord_voice"])

            Text {
                Layout.fillWidth: true
                text: "Credentials below need an app restart to connect, except Spotify sign-in."
                color: Theme.textFaint
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontMicro
                wrapMode: Text.WordWrap
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "♥"
                key: "show_heart_rate"
                label: "Heart rate (Pulsoid)"
                hint: "Get a token at pulsoid.net → Settings → API"
            }

            TextInput {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                visible: Bridge.options.show_heart_rate === true
                label: "Pulsoid access token"
                placeholder: "paste token"
                value: Bridge.options.pulsoid_token || ""
                onCommitted: (v) => Bridge.setTextOption("pulsoid_token", v)
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "♫"
                key: "show_spotify"
                label: "Spotify"
                hint: "Liked/explicit/shuffle/repeat/device/volume - replaces generic Now Playing"
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                visible: Bridge.options.show_spotify === true
                spacing: Theme.gapTight

                TextInput {
                    Layout.fillWidth: true
                    label: "Spotify Client ID"
                    hint: "developer.spotify.com/dashboard → Create app → redirect URI http://127.0.0.1:8888/callback"
                    placeholder: "client id"
                    value: Bridge.options.spotify_client_id || ""
                    onCommitted: (v) => Bridge.setTextOption("spotify_client_id", v)
                }

                ActionButton {
                    text: Bridge.spotifyAuthenticated ? "signed in" : "sign in"
                    icon: "↪"
                    onClicked: Bridge.spotifyLogin()
                }

                TextInput {
                    Layout.fillWidth: true
                    label: "Chatbox template"
                    hint: "Tokens: {title} {artist}"
                    placeholder: "{title} - {artist}"
                    value: Bridge.options.spotify_template || ""
                    onCommitted: (v) => Bridge.setTextOption("spotify_template", v)
                }
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "▶"
                key: "show_twitch"
                label: "Twitch"
                hint: "Live status, category, viewers, followers - read-only, no viewer login"
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                visible: Bridge.options.show_twitch === true
                spacing: Theme.gapTight

                TextInput {
                    label: "Twitch Client ID"
                    hint: "Free app at dev.twitch.tv/console/apps"
                    value: Bridge.options.twitch_client_id || ""
                    onCommitted: (v) => Bridge.setTextOption("twitch_client_id", v)
                }
                TextInput {
                    label: "Twitch Client Secret"
                    value: Bridge.options.twitch_client_secret || ""
                    onCommitted: (v) => Bridge.setTextOption("twitch_client_secret", v)
                }
                TextInput {
                    label: "Your Twitch username"
                    value: Bridge.options.twitch_username || ""
                    onCommitted: (v) => Bridge.setTextOption("twitch_username", v)
                }
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "♪"
                key: "show_tiktok"
                label: "TikTok Live"
                hint: "Viewer count, follows and gifts while you're live - public feed, no login"
            }

            TextInput {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                visible: Bridge.options.show_tiktok === true
                label: "TikTok username"
                placeholder: "@yourname"
                value: Bridge.options.tiktok_username || ""
                onCommitted: (v) => Bridge.setTextOption("tiktok_username", v)
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "◈"
                key: "show_discord_voice"
                label: "Discord voice channel"
                hint: "Who's in your voice channel - via a bot, not a self-bot"
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                visible: Bridge.options.show_discord_voice === true
                spacing: Theme.gapTight

                TextInput {
                    label: "Bot token"
                    hint: "discord.com/developers → your app → Bot. Enable Server Members + Voice States intents, invite it to your server."
                    value: Bridge.options.discord_bot_token || ""
                    onCommitted: (v) => Bridge.setTextOption("discord_bot_token", v)
                }
                TextInput {
                    label: "Your Discord user ID"
                    hint: "Enable Developer Mode, right-click your name, Copy User ID"
                    value: Bridge.options.discord_watch_user_id || ""
                    onCommitted: (v) => Bridge.setTextOption("discord_watch_user_id", v)
                }
            }
        }

        // TTS --------------------------------------------------------------------------

        CollapsibleSection {
            title: "TTS & voice"
            subtitle: Bridge.ttsAvailable ? onCount(["tts_enabled"]) : "no engine found"

            Text {
                Layout.fillWidth: true
                visible: !Bridge.ttsAvailable
                text: "No local TTS engine found - install espeak-ng, or piper for better quality."
                color: Theme.warn
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontMicro
                wrapMode: Text.WordWrap
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "◐"
                key: "tts_enabled"
                label: "Text to speech"
                hint: "Local synthesis only - " + Bridge.ttsEngine
            }

            OptionSwitch {
                Layout.fillWidth: true
                Layout.leftMargin: 46
                icon: "▶"
                key: "tts_speak_chatbox"
                label: "Speak the chatbox line"
                hint: "Reads each new status out loud as it's sent"
            }
        }

        // IntelliChat --------------------------------------------------------------------

        CollapsibleSection {
            title: "IntelliChat"
            subtitle: Bridge.options.intellichat_enabled === true ? "on · AI" : "off · AI"

            Text {
                Layout.fillWidth: true
                text: "Off by default. Sends your composed chatbox text to an AI API to fix "
                    + "spelling and shorten it to fit - needs your own API key, nothing bundled."
                color: Theme.textFaint
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontMicro
                wrapMode: Text.WordWrap
            }

            OptionSwitch {
                Layout.fillWidth: true
                icon: "✨"
                key: "intellichat_enabled"
                label: "Enable IntelliChat"
                hint: "Spelling fix + smart shortening before each send"
            }

            ColumnLayout {
                Layout.fillWidth: true
                visible: Bridge.options.intellichat_enabled === true
                spacing: Theme.gapTight

                TextInput {
                    label: "API key"
                    hint: "Any OpenAI-compatible endpoint - OpenAI itself, or your own server"
                    value: Bridge.options.intellichat_api_key || ""
                    onCommitted: (v) => Bridge.setTextOption("intellichat_api_key", v)
                }
                TextInput {
                    label: "API base URL"
                    value: Bridge.options.intellichat_api_base || ""
                    onCommitted: (v) => Bridge.setTextOption("intellichat_api_base", v)
                }
                TextInput {
                    label: "Model"
                    value: Bridge.options.intellichat_model || ""
                    onCommitted: (v) => Bridge.setTextOption("intellichat_model", v)
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: Theme.gapTight
            Layout.bottomMargin: Theme.gap
            wrapMode: Text.WordWrap
            text: "Not included: Soundpad and Voicemod are Windows-only apps with no Linux "
                + "client at all - nothing here to connect to."
            color: Theme.textFaint
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontMicro
        }
    }
}
