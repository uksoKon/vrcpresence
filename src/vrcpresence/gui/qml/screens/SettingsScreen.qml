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

        // Discord ----------------------------------------------------------

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: discord.implicitHeight + Theme.gapLoose * 2
            padding: Theme.gapLoose

            ColumnLayout {
                id: discord
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Theme.gap

                Text {
                    text: "DISCORD"
                    color: Theme.accent
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

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
                    icon: "\u25C9"
                    label: "Rich Presence"
                    hint: "Show your world on your Discord profile"
                    checked: Bridge.discordEnabled
                    onToggled: (v) => Bridge.setDiscordEnabled(v)
                }

                SettingSwitch {
                    Layout.fillWidth: true
                    icon: "\u25CB"
                    label: "Show players"
                    hint: "Include the instance headcount"
                    checked: Bridge.showPlayers
                    onToggled: (v) => Bridge.setShowPlayers(v)
                }

                SettingSwitch {
                    Layout.fillWidth: true
                    icon: "\u2197"
                    label: "Join button"
                    hint: "Let friends click through into your instance"
                    checked: Bridge.allowJoin
                    onToggled: (v) => Bridge.setAllowJoin(v)
                }

                SettingSwitch {
                    Layout.fillWidth: true
                    icon: "\u25A3"
                    label: "Hide private instances"
                    hint: "Broadcast public instances only"
                    checked: Bridge.hidePrivate
                    onToggled: (v) => Bridge.setHidePrivate(v)
                }

                SettingSwitch {
                    Layout.fillWidth: true
                    icon: "\u2298"
                    label: "Private mode"
                    hint: "Hide everything without closing the app"
                    checked: Bridge.privateMode
                    onToggled: (v) => Bridge.setPrivateMode(v)
                }
            }
        }

        // Desktop -------------------------------------------------------------

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: desktop.implicitHeight + Theme.gapLoose * 2
            padding: Theme.gapLoose

            ColumnLayout {
                id: desktop
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Theme.gap

                Text {
                    text: "DESKTOP"
                    color: Theme.accent
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                SettingSwitch {
                    Layout.fillWidth: true
                    icon: "\u2709"
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
                    spacing: Theme.gapTight

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
        }

        // Paths ----------------------------------------------------------------

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: paths.implicitHeight + Theme.gapLoose * 2
            padding: Theme.gapLoose

            ColumnLayout {
                id: paths
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Theme.gapTight

                Text {
                    text: "DETECTED"
                    color: Theme.accent
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                Text {
                    Layout.fillWidth: true
                    text: Bridge.logPath || "No VRChat log found"
                    color: Bridge.logFound ? Theme.textDim : Theme.bad
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                    wrapMode: Text.WrapAnywhere
                }
            }
        }
    }
}
