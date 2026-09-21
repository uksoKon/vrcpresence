import QtQuick
import ".."

Column {
    id: nav

    property var entries: []
    property int currentIndex: 0

    spacing: 2

    Repeater {
        model: nav.entries

        Rectangle {
            required property int index
            required property var modelData

            width: nav.width
            height: 40
            radius: Theme.radiusSmall
            color: index === nav.currentIndex
                ? Theme.accent
                : (hover.hovered ? Theme.surfaceAlt : "transparent")

            Behavior on color {
                ColorAnimation { duration: Theme.animFast }
            }

            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: Theme.gap
                spacing: Theme.gap

                Text {
                    text: modelData.icon
                    color: index === nav.currentIndex ? Theme.accentText : Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontBody
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: modelData.label
                    color: index === nav.currentIndex ? Theme.accentText : Theme.text
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontBody
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            HoverHandler { id: hover }

            TapHandler {
                onTapped: nav.currentIndex = index
            }
        }
    }
}
