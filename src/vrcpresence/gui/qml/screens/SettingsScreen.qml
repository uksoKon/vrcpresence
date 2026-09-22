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
        spacing: Theme.gapTight

        // Discord --------------------------------------------------------------

        CollapsibleSection {
            title: "Discord"
            subtitle: Bridge.discordStatus
            open: true

            TextInput {
                Layout.fillWidth: true
                label: "Application ID"
                hint: "Rich Presence needs an app of your own: discord.com/developers "
                    + "> New Application > copy Application ID. Upload icons named 'vr', "
                    + "'desktop' and 'vrchat' under Rich Presence > Art Assets."
                placeholder: "e.g. 1234567890123456789"
                value: Bridge.discordAppId
                onCommitted: (v) => Bridge.setDiscordAppId(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "◉"
                label: "Rich Presence"
                hint: "Show your world on your Discord profile"
                checked: Bridge.discordEnabled
                onToggled: (v) => Bridge.setDiscordEnabled(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "○"
                label: "Show players"
                hint: "Include the instance headcount"
                checked: Bridge.showPlayers
                onToggled: (v) => Bridge.setShowPlayers(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "↗"
                label: "Join button"
                hint: "Let friends click through into your instance"
                checked: Bridge.allowJoin
                onToggled: (v) => Bridge.setAllowJoin(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "▣"
                label: "Hide private instances"
                hint: "Broadcast public instances only"
                checked: Bridge.hidePrivate
                onToggled: (v) => Bridge.setHidePrivate(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "⊘"
                label: "Private mode"
                hint: "Hide everything without closing the app"
                checked: Bridge.privateMode
                onToggled: (v) => Bridge.setPrivateMode(v)
            }
        }

        // Desktop ----------------------------------------------------------------

        CollapsibleSection {
            title: "Desktop"
            subtitle: Bridge.historyEnabled ? "history on" : "history off"

            SettingSwitch {
                Layout.fillWidth: true
                icon: "✉"
                label: "Notifications"
                hint: "Desktop popup when someone joins or leaves"
                checked: Bridge.notificationsEnabled
                onToggled: (v) => Bridge.setNotificationsEnabled(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "◴"
                label: "History"
                hint: "Keep a record of worlds you visit"
                checked: Bridge.historyEnabled
                onToggled: (v) => Bridge.setHistoryEnabled(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "✕"
                label: "Session only"
                hint: "Wipe history when VRChat closes - nothing kept between sessions"
                checked: Bridge.sessionHistoryOnly
                onToggled: (v) => Bridge.setSessionHistoryOnly(v)
            }

            RowLayout {
                Layout.fillWidth: true

                Item { Layout.fillWidth: true }

                ActionButton {
                    id: clearButton
                    text: "Clear history"
                    icon: "✕"
                    danger: true
                    confirming: armed

                    property bool armed: false

                    Timer {
                        id: disarm
                        interval: 4000
                        onTriggered: clearButton.armed = false
                    }

                    onClicked: {
                        if (armed) {
                            Bridge.clearHistory();
                            armed = false;
                            disarm.stop();
                        } else {
                            armed = true;
                            disarm.restart();
                        }
                    }
                }
            }
        }

        // App options / Standalone -------------------------------------------------

        CollapsibleSection {
            title: "App options"
            subtitle: Bridge.oscHost + ":" + Bridge.oscPort

            SettingSwitch {
                Layout.fillWidth: true
                icon: "⏻"
                label: "Launch on login"
                hint: "Starts the background service (presence + chatbox), not the window"
                checked: Bridge.autostartEnabled
                onToggled: (v) => Bridge.setAutostart(v)
            }

            Text {
                Layout.fillWidth: true
                text: "OSC destination (Standalone): default 127.0.0.1 talks to VRChat on this "
                    + "machine. Point it at a Quest's IP to run this on a separate PC."
                color: Theme.textFaint
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontMicro
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.gapTight

                TextInput {
                    Layout.fillWidth: true
                    label: "Host"
                    value: Bridge.oscHost
                    onCommitted: (v) => Bridge.setOscHost(v)
                }

                TextInput {
                    Layout.preferredWidth: 100
                    label: "Port"
                    value: String(Bridge.oscPort)
                    onCommitted: (v) => Bridge.setOscPort(v)
                }
            }
        }

        // Paths --------------------------------------------------------------------

        CollapsibleSection {
            title: "Detected paths"
            subtitle: Bridge.logFound ? "log found" : "no log"

            Text {
                Layout.fillWidth: true
                text: Bridge.logPath || "No VRChat log found"
                color: Bridge.logFound ? Theme.textDim : Theme.bad
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontMicro
                wrapMode: Text.WrapAnywhere
            }
        }

        Item { Layout.preferredHeight: Theme.gap }
    }
}
