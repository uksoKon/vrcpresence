import QtQuick
import QtQuick.Shapes
import ".."

Card {
    id: card

    property string worldName: ""
    property string imageUrl: ""
    property int players: 0
    property int capacity: 0
    property string mode: ""
    property bool inWorld: false

    highlighted: inWorld

    Row {
        anchors.fill: parent
        spacing: Theme.gapLoose

        Item {
            width: 128
            height: 128
            anchors.verticalCenter: parent.verticalCenter

            Shape {
                anchors.fill: parent
                visible: !card.inWorld
                ShapePath {
                    strokeColor: Theme.border
                    strokeWidth: 2
                    fillColor: "transparent"
                    strokeStyle: ShapePath.DashLine
                    dashPattern: [4, 4]
                    PathAngleArc {
                        centerX: 64
                        centerY: 64
                        radiusX: 62
                        radiusY: 62
                        startAngle: 0
                        sweepAngle: 360
                    }
                }
            }

            Rectangle {
                anchors.centerIn: parent
                width: 112
                height: 112
                radius: width / 2
                color: Theme.surfaceAlt
                clip: true

                Image {
                    anchors.fill: parent
                    source: card.imageUrl
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    visible: card.imageUrl !== "" && status === Image.Ready
                }

                Text {
                    anchors.centerIn: parent
                    visible: card.imageUrl === ""
                    text: "◌"
                    color: Theme.textDim
                    font.pixelSize: 34
                }
            }
        }

        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: Theme.gap
            width: parent.width - 128 - Theme.gapLoose

            Text {
                text: card.inWorld ? (card.worldName || "Loading world...") : "Not in a world"
                color: Theme.text
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontHero
                elide: Text.ElideRight
                width: parent.width
            }

            Text {
                visible: !card.inWorld
                text: "Start VRChat and your status appears here"
                color: Theme.textDim
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontBody
            }

            Row {
                spacing: Theme.gapTight
                visible: card.inWorld

                Pill {
                    text: card.capacity > 0
                        ? card.players + " / " + card.capacity + " players"
                        : card.players + (card.players === 1 ? " player" : " players")
                    icon: "◉"
                    tint: Theme.accent
                    filled: true
                }

                Pill {
                    visible: card.mode !== ""
                    text: card.mode
                    icon: card.mode === "VR" ? "⬛" : "▭"
                    tint: Theme.accentMuted
                }
            }
        }
    }
}
