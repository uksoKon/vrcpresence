import VrcPresence
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

ColumnLayout {
    spacing: Theme.gap

    // Live preview of exactly what goes in-game ---------------------------

    Card {
        Layout.fillWidth: true
        Layout.fillHeight: false
        Layout.preferredHeight: 124
        Layout.maximumHeight: 124
        padding: Theme.gap
        highlighted: Bridge.chatboxEnabled

        ColumnLayout {
            anchors.fill: parent
            spacing: Theme.gapTight

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: "Chatbox preview"
                    color: Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                Item { Layout.fillWidth: true }

                Pill {
                    text: Bridge.chatboxEnabled ? "sending" : "paused"
                    icon: "●"
                    tint: Bridge.chatboxEnabled ? Theme.good : Theme.textFaint
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Theme.radiusSmall
                color: Theme.surfaceAlt
                border.width: 1
                border.color: Theme.border

                Text {
                    anchors.fill: parent
                    anchors.margins: Theme.gap
                    text: Bridge.chatboxPreview || "Set a template below"
                    color: Bridge.chatboxPreview ? Theme.text : Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontBody
                    wrapMode: Text.Wrap
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    // Options ---------------------------------------------------------------

    Card {
        Layout.fillWidth: true
        Layout.fillHeight: true
        padding: Theme.gap

        ColumnLayout {
            anchors.fill: parent
            spacing: Theme.gapTight

            SettingSwitch {
                Layout.fillWidth: true
                icon: "✉"
                label: "Send to chatbox"
                hint: "Push this status into VRChat every " + Bridge.chatboxInterval + "s"
                checked: Bridge.chatboxEnabled
                onToggled: (v) => Bridge.setChatboxEnabled(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "♪"
                label: "Now playing"
                hint: Bridge.nowPlaying
                checked: Bridge.chatboxMedia
                onToggled: (v) => Bridge.setChatboxMedia(v)
            }

            TextInput {
                Layout.fillWidth: true
                Layout.leftMargin: Theme.gap
                Layout.rightMargin: Theme.gap
                label: "Template"
                hint: "{world} {players} {capacity} {mode} {time} {song} {title} {artist} {player}"
                placeholder: "{world} | {players} here | {song}"
                value: Bridge.chatboxTemplate
                onCommitted: (v) => Bridge.setChatboxTemplate(v)
            }

            SettingSwitch {
                Layout.fillWidth: true
                icon: "…"
                label: "Typing indicator"
                hint: "Show the typing bubble while a status is queued"
                checked: Bridge.chatboxTyping
                onToggled: (v) => Bridge.setChatboxTyping(v)
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: Theme.gap
                Layout.rightMargin: Theme.gap
                spacing: Theme.gapTight

                Text {
                    text: "Presets"
                    color: Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: "every " + Bridge.chatboxInterval + "s"
                    color: Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                ActionButton {
                    text: "−"
                    onClicked: Bridge.nudgeChatboxInterval(-1)
                }

                ActionButton {
                    text: "+"
                    onClicked: Bridge.nudgeChatboxInterval(1)
                }

                ActionButton {
                    text: "send now"
                    icon: "↪"
                    onClicked: Bridge.sendChatboxNow()
                }
            }

            Flow {
                Layout.fillWidth: true
                Layout.leftMargin: Theme.gap
                Layout.rightMargin: Theme.gap
                spacing: Theme.gapTight

                Repeater {
                    model: [
                        { name: "world", value: "{world} | {players} here" },
                        { name: "music", value: "♪ {song}" },
                        { name: "both", value: "{world} | ♪ {song}" },
                        { name: "full", value: "{world} ({players}) | {mode} | ♪ {song}" },
                        { name: "clock", value: "{time} | {world}" }
                    ]

                    ActionButton {
                        required property var modelData
                        text: modelData.name
                        onClicked: Bridge.setChatboxTemplate(modelData.value)
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}
