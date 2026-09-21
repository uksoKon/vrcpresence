import QtQuick
import ".."

Rectangle {
    property string label: ""
    property string value: ""
    property color valueColor: Theme.text

    radius: Theme.radiusSmall
    color: Theme.surfaceAlt
    border.width: 1
    border.color: Theme.border

    Column {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Theme.gap
        anchors.rightMargin: Theme.gap
        spacing: 3

        Text {
            text: label
            color: Theme.textFaint
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontMicro
            elide: Text.ElideRight
            width: parent.width
        }

        Text {
            text: value
            color: valueColor
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontLead
            elide: Text.ElideRight
            width: parent.width
        }
    }
}
