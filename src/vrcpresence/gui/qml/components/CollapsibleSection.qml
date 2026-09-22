import QtQuick
import QtQuick.Layouts
import ".."

// One category, collapsed to a single header row until tapped open. Turns a
// long wall of always-visible settings into something you can scan in a
// glance and only expand what you actually came to change.
Rectangle {
    id: section

    property string title: ""
    property string subtitle: ""
    property bool open: false
    default property alias content: body.data

    Layout.fillWidth: true
    Layout.preferredHeight: header.height + (open ? body.implicitHeight + Theme.gap : 0) + Theme.gapTight
    radius: Theme.radiusCard
    color: Theme.surface
    border.width: 1
    border.color: open ? Theme.accent : Theme.border
    clip: true

    Behavior on Layout.preferredHeight {
        NumberAnimation { duration: Theme.animBase; easing.type: Easing.OutCubic }
    }
    Behavior on border.color {
        ColorAnimation { duration: Theme.animFast }
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 0

        Rectangle {
            id: header
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            color: "transparent"
            radius: Theme.radiusCard

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Theme.gapLoose
                anchors.rightMargin: Theme.gapLoose
                spacing: Theme.gapTight

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: section.title
                        color: Theme.text
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontBody
                    }

                    Text {
                        visible: section.subtitle !== ""
                        text: section.subtitle
                        color: Theme.textFaint
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontMicro
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                Text {
                    text: section.open ? "−" : "+"
                    color: section.open ? Theme.accent : Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontLead
                }
            }

            TapHandler {
                onTapped: section.open = !section.open
            }
        }

        ColumnLayout {
            id: body
            Layout.fillWidth: true
            Layout.leftMargin: Theme.gapLoose
            Layout.rightMargin: Theme.gapLoose
            Layout.bottomMargin: Theme.gap
            spacing: Theme.gapTight
            visible: section.open
        }
    }
}
