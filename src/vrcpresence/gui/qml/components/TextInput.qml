import QtQuick
import QtQuick.Controls
import ".."

Item {
    id: control

    property string label: ""
    property string hint: ""
    property string placeholder: ""
    property string value: ""

    signal committed(string value)

    implicitHeight: column.height

    Column {
        id: column
        width: parent.width
        spacing: 6

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
            wrapMode: Text.WordWrap
            width: parent.width
        }

        Rectangle {
            width: parent.width
            height: 34
            radius: Theme.radiusSmall
            color: Theme.surfaceAlt
            border.width: 1
            border.color: field.activeFocus ? Theme.accent : Theme.border

            Behavior on border.color {
                ColorAnimation { duration: Theme.animFast }
            }

            TextField {
                id: field
                anchors.fill: parent
                anchors.leftMargin: Theme.gapTight
                anchors.rightMargin: Theme.gapTight
                text: control.value
                placeholderText: control.placeholder
                color: Theme.text
                placeholderTextColor: Theme.textDim
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontSmall
                verticalAlignment: TextInput.AlignVCenter
                background: null

                onEditingFinished: control.committed(text)
            }
        }
    }
}
