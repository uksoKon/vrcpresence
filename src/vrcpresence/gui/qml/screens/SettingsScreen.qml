import VrcPresence
import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Flickable {
    contentHeight: column.height
    clip: true

    Column {
        id: column
        width: parent.width
        spacing: Theme.gap

        Card {
            width: parent.width
            height: toggles.height + Theme.gapLoose * 2
            padding: Theme.gapLoose

            Column {
                id: toggles
                width: parent.width
                spacing: Theme.gap

                Text {
                    text: "Discord"
                    color: Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontSmall
                }

                SettingSwitch {
                    width: parent.width
                    label: "Rich Presence"
                    hint: "Show your world on your Discord profile"
                    checked: Bridge.discordEnabled
                    onToggled: Bridge.setDiscordEnabled(checked)
                }

                SettingSwitch {
                    width: parent.width
                    label: "Show players"
                    hint: "Include the instance headcount"
                    checked: Bridge.showPlayers
                    onToggled: Bridge.setShowPlayers(checked)
                }

                SettingSwitch {
                    width: parent.width
                    label: "Join button"
                    hint: "Let friends click through into your instance"
                    checked: Bridge.allowJoin
                    onToggled: Bridge.setAllowJoin(checked)
                }

                SettingSwitch {
                    width: parent.width
                    label: "Private mode"
                    hint: "Hide everything without closing the app"
                    checked: Bridge.privateMode
                    onToggled: Bridge.setPrivateMode(checked)
                }
            }
        }

        Card {
            width: parent.width
            height: others.height + Theme.gapLoose * 2
            padding: Theme.gapLoose

            Column {
                id: others
                width: parent.width
                spacing: Theme.gap

                Text {
                    text: "In-game and desktop"
                    color: Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontSmall
                }

                SettingSwitch {
                    width: parent.width
                    label: "Chatbox status"
                    hint: "Push a rotating status into VRChat's chatbox"
                    checked: Bridge.chatboxEnabled
                    onToggled: Bridge.setChatboxEnabled(checked)
                }

                SettingSwitch {
                    width: parent.width
                    label: "Notifications"
                    hint: "Desktop popup when someone joins or leaves"
                    checked: Bridge.notificationsEnabled
                    onToggled: Bridge.setNotificationsEnabled(checked)
                }

                SettingSwitch {
                    width: parent.width
                    label: "History"
                    hint: "Keep a local record of worlds you visit"
                    checked: Bridge.historyEnabled
                    onToggled: Bridge.setHistoryEnabled(checked)
                }
            }
        }

        Card {
            width: parent.width
            height: paths.height + Theme.gapLoose * 2
            padding: Theme.gapLoose

            Column {
                id: paths
                width: parent.width
                spacing: Theme.gapTight

                Text {
                    text: "Detected paths"
                    color: Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontSmall
                }

                Text {
                    text: Bridge.logPath || "No VRChat log found"
                    color: Bridge.logFound ? Theme.text : Theme.bad
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontSmall
                    wrapMode: Text.WrapAnywhere
                    width: parent.width
                }
            }
        }
    }
}
