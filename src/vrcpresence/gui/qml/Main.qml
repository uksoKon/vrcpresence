import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import "components"
import "screens"

Window {
    id: root
    width: 940
    height: 620
    minimumWidth: 780
    minimumHeight: 520
    visible: true
    title: "vrcpresence"
    color: Theme.background

    Row {
        anchors.fill: parent

        Rectangle {
            width: 210
            height: parent.height
            color: Theme.surface

            Column {
                anchors.fill: parent
                anchors.margins: Theme.gap
                spacing: Theme.gapLoose

                Row {
                    spacing: Theme.gapTight
                    height: 40

                    Text {
                        text: "◉"
                        color: Theme.accent
                        font.pixelSize: Theme.fontTitle
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: "vrcpresence"
                        color: Theme.text
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontBody
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                SidebarNav {
                    id: nav
                    width: parent.width
                    entries: [
                        { icon: "◉", label: "Status" },
                        { icon: "◴", label: "History" },
                        { icon: "⚙", label: "Settings" },
                        { icon: "ⓘ", label: "About" }
                    ]
                }
            }
        }

        Item {
            width: parent.width - 210
            height: parent.height

            StackLayout {
                anchors.fill: parent
                anchors.margins: Theme.gapLoose
                currentIndex: nav.currentIndex

                StatusScreen {}
                HistoryScreen {}
                SettingsScreen {}
                AboutScreen {}
            }
        }
    }
}
