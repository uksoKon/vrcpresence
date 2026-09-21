import QtQuick
import ".."

Item {
    id: control

    property string label: ""
    property string hint: ""
    property bool checked: false

    signal toggled(bool checked)

    implicitHeight: 42

    Column {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        spacing: 2
        width: parent.width - 52

        Text {
            text: control.label
            color: Theme.text
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontBody
        }

        Text {
            visible: control.hint !== ""
            text: control.hint
            color: Theme.textDim
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontSmall
            elide: Text.ElideRight
            width: parent.width
        }
    }

    Rectangle {
        id: track
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        width: 44
        height: 24
        radius: Theme.radiusPill
        color: control.checked ? Theme.accent : Theme.surfaceAlt
        border.width: 1
        border.color: control.checked ? Theme.accent : Theme.border

        Behavior on color {
            ColorAnimation { duration: Theme.animFast }
        }

        Rectangle {
            width: 18
            height: 18
            radius: width / 2
            color: control.checked ? Theme.accentText : Theme.textDim
            anchors.verticalCenter: parent.verticalCenter
            x: control.checked ? track.width - width - 3 : 3

            Behavior on x {
                NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic }
            }
        }
    }

    TapHandler {
        onTapped: {
            control.checked = !control.checked;
            control.toggled(control.checked);
        }
    }
}
