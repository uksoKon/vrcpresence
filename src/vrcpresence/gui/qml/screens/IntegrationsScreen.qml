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

    ColumnLayout {
        id: column
        width: parent.width
        spacing: Theme.gap

        Text {
            Layout.fillWidth: true
            text: "Mode: components (turn any of these on) instead of a single "
                + "template. Switch it on in Chatbox → Send to chatbox."
            color: Theme.textFaint
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontMicro
            wrapMode: Text.WordWrap
        }

        OptionSwitch {
            Layout.fillWidth: true
            icon: "≡"
            key: "chatbox_components"
            label: "Assemble from components"
            hint: "Off = single template on the Chatbox tab. On = everything below."
        }

        // You ------------------------------------------------------------------

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: youCol.implicitHeight + Theme.gapLoose * 2
            padding: Theme.gapLoose

            ColumnLayout {
                id: youCol
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Theme.gapTight

                Text {
                    text: "YOU"
                    color: Theme.accent
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

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
        }

        // Hardware ---------------------------------------------------------------

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: hwCol.implicitHeight + Theme.gapLoose * 2
            padding: Theme.gapLoose

            ColumnLayout {
                id: hwCol
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Theme.gapTight

                Text {
                    text: "HARDWARE"
                    color: Theme.accent
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

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
        }

        // Not available on Linux --------------------------------------------------

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: skippedCol.implicitHeight + Theme.gapLoose * 2
            padding: Theme.gapLoose

            ColumnLayout {
                id: skippedCol
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: 4

                Text {
                    text: "FROM MAGICCHATBOX, NOT INCLUDED"
                    color: Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Soundpad and Voicemod are Windows-only apps. Tracker battery and VR "
                        + "performance need the OpenVR/SteamVR overlay API, which isn't exposed the "
                        + "same way under Proton. Heart rate (Pulsoid), Spotify, Twitch and TikTok "
                        + "all need paid or OAuth-gated accounts. IntelliChat is AI-based - skipped on request."
                    color: Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                    lineHeight: 1.3
                }
            }
        }
    }
}
