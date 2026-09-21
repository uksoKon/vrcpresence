import VrcPresence
import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Column {
    spacing: Theme.gap

    WorldCard {
        width: parent.width
        height: 176
        inWorld: Bridge.inWorld
        worldName: Bridge.worldName
        imageUrl: Bridge.worldImageUrl
        players: Bridge.playerCount
        capacity: Bridge.worldCapacity
        mode: Bridge.mode
    }

    Card {
        width: parent.width
        height: parent.height - 176 - Theme.gap * 2 - 34
        padding: Theme.gap

        Column {
            anchors.fill: parent
            spacing: Theme.gapTight

            Text {
                text: "In this instance"
                color: Theme.textDim
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontSmall
            }

            ListView {
                width: parent.width
                height: parent.height - 24
                clip: true
                model: Bridge.players
                spacing: 2

                delegate: Rectangle {
                    required property string modelData
                    width: ListView.view.width
                    height: 30
                    radius: Theme.radiusSmall
                    color: "transparent"

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: Theme.gapTight
                        text: modelData
                        color: Theme.text
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontBody
                    }
                }

                Text {
                    anchors.centerIn: parent
                    visible: parent.count === 0
                    text: "Nobody here yet"
                    color: Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontBody
                }
            }
        }
    }

    Row {
        spacing: Theme.gapTight

        Pill {
            text: Bridge.logFound ? "log" : "no log"
            icon: "●"
            tint: Bridge.logFound ? Theme.good : Theme.bad
        }

        Pill {
            text: Bridge.discordConnected ? "discord" : "discord off"
            icon: "●"
            tint: Bridge.discordConnected ? Theme.good : Theme.textDim
        }

        Pill {
            text: Bridge.vrchatAuthenticated ? "api" : "api off"
            icon: "●"
            tint: Bridge.vrchatAuthenticated ? Theme.good : Theme.textDim
        }

        Pill {
            visible: Bridge.privateMode
            text: "private"
            icon: "●"
            tint: Theme.accent
            filled: true
        }
    }
}
