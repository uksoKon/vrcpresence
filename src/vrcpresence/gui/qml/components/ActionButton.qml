import QtQuick
import ".."

Rectangle {
    id: button

    property string text: ""
    property string icon: ""
    property bool danger: false
    property bool confirming: false

    signal clicked()

    implicitWidth: row.implicitWidth + Theme.gapLoose
    implicitHeight: 32
    radius: Theme.radiusSmall
    color: hover.hovered ? Theme.surfaceAlt : "transparent"
    border.width: 1
    border.color: confirming ? Theme.bad : (danger ? Theme.bad : Theme.border)

    Behavior on color {
        ColorAnimation { duration: Theme.animFast }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: Theme.gapTight

        Text {
            visible: button.icon !== ""
            text: button.icon
            color: button.danger ? Theme.bad : Theme.textDim
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontSmall
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: button.confirming ? "click again to confirm" : button.text
            color: button.danger ? Theme.bad : Theme.text
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontSmall
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    HoverHandler {
        id: hover
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        onTapped: button.clicked()
    }
}
