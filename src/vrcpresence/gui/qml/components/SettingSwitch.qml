import QtQuick
import QtQuick.Layouts
import ".."

Rectangle {
    id: control

    property string label: ""
    property string hint: ""
    property string icon: "◉"
    property bool checked: false

    signal toggled(bool checked)

    implicitHeight: 62
    radius: Theme.radiusCard
    color: hover.hovered ? Theme.surfaceAlt : "transparent"

    Behavior on color {
        ColorAnimation { duration: Theme.animFast }
    }

    HoverHandler { id: hover }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Theme.gap
        anchors.rightMargin: Theme.gap
        spacing: Theme.gap

        Rectangle {
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            Layout.alignment: Qt.AlignVCenter
            radius: Theme.radiusSmall
            color: control.checked ? Theme.accentSoft : Theme.surfaceAlt

            Behavior on color {
                ColorAnimation { duration: Theme.animFast }
            }

            Text {
                anchors.centerIn: parent
                text: control.icon
                color: control.checked ? Theme.accent : Theme.textFaint
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontBody
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 3

            Text {
                Layout.fillWidth: true
                text: control.label
                color: Theme.text
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontBody
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                visible: control.hint !== ""
                text: control.hint
                color: Theme.textFaint
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontMicro
                elide: Text.ElideRight
            }
        }

        Rectangle {
            id: track
            Layout.preferredWidth: 46
            Layout.preferredHeight: 26
            Layout.alignment: Qt.AlignVCenter
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
                color: control.checked ? Theme.accentText : Theme.textFaint
                anchors.verticalCenter: parent.verticalCenter
                x: control.checked ? track.width - width - 4 : 4

                Behavior on x {
                    NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic }
                }
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
