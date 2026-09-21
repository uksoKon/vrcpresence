import QtQuick
import ".."

Rectangle {
    id: pill

    property string text: ""
    property string icon: ""
    property color tint: Theme.textDim
    property bool filled: false

    implicitHeight: 24
    implicitWidth: row.implicitWidth + Theme.gap
    radius: Theme.radiusPill
    color: filled ? tint : Theme.surfaceAlt
    border.width: filled ? 0 : 1
    border.color: Theme.border

    Behavior on color {
        ColorAnimation { duration: Theme.animFast }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6

        Text {
            visible: pill.icon !== ""
            text: pill.icon
            color: pill.filled ? Theme.accentText : pill.tint
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontSmall
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: pill.text
            color: pill.filled ? Theme.accentText : Theme.text
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontSmall
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
