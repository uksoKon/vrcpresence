import VrcPresence
import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Column {
    spacing: Theme.gap

    Card {
        width: parent.width
        height: 78
        padding: Theme.gap

        Row {
            anchors.fill: parent
            spacing: Theme.gapLoose

            Repeater {
                model: Bridge.historyTotals

                Column {
                    required property var modelData
                    spacing: 4

                    Text {
                        text: modelData.value
                        color: Theme.accent
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontTitle
                    }

                    Text {
                        text: modelData.label
                        color: Theme.textDim
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontSmall
                    }
                }
            }
        }
    }

    Card {
        width: parent.width
        height: parent.height - 78 - Theme.gap
        padding: Theme.gap

        ListView {
            anchors.fill: parent
            clip: true
            model: Bridge.visits
            spacing: 2

            delegate: Rectangle {
                required property var modelData
                width: ListView.view.width
                height: 38
                radius: Theme.radiusSmall
                color: hover.hovered ? Theme.surfaceAlt : "transparent"

                HoverHandler { id: hover }

                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: Theme.gapTight
                    anchors.rightMargin: Theme.gapTight
                    spacing: Theme.gap

                    Text {
                        text: modelData.when
                        color: Theme.textDim
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontSmall
                        width: 110
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: modelData.name
                        color: Theme.text
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontBody
                        elide: Text.ElideRight
                        width: parent.width - 110 - 130 - Theme.gap * 2
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Pill {
                        text: modelData.duration
                        tint: Theme.textDim
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Pill {
                        text: "peak " + modelData.peak
                        tint: Theme.accentMuted
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: parent.count === 0
                text: "No worlds visited yet"
                color: Theme.textDim
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontBody
            }
        }
    }
}
