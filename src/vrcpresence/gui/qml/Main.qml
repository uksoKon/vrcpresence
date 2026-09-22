import VrcPresence
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import "components"
import "screens"

Window {
    id: root
    width: 980
    height: 640
    minimumWidth: 860
    minimumHeight: 560
    visible: true
    title: "vrcpresence"
    color: "transparent"

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusCard
        color: Theme.background
        border.width: 1
        border.color: Theme.border

        RowLayout {
            anchors.fill: parent
            anchors.margins: 1
            spacing: 0

            // Sidebar ------------------------------------------------------

            Rectangle {
                Layout.preferredWidth: Theme.sidebarWidth
                Layout.fillHeight: true
                color: Theme.sidebar
                topLeftRadius: Theme.radiusCard
                bottomLeftRadius: Theme.radiusCard

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Theme.gap
                    spacing: Theme.gapLoose

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        spacing: Theme.gapTight

                        Rectangle {
                            Layout.preferredWidth: 10
                            Layout.preferredHeight: 10
                            radius: 5
                            color: Bridge.vrchatRunning ? Theme.good : Theme.textFaint

                            Behavior on color {
                                ColorAnimation { duration: Theme.animBase }
                            }
                        }

                        Text {
                            text: "vrcpresence"
                            color: Theme.text
                            font.family: Theme.fontMono
                            font.pixelSize: Theme.fontBody
                        }

                        Item { Layout.fillWidth: true }
                    }

                    SidebarNav {
                        id: nav
                        Layout.fillWidth: true
                        entries: [
                            { icon: "◉", label: "Status" },
                            { icon: "✉", label: "Chatbox" },
                            { icon: "✦", label: "Integrations" },
                            { icon: "◴", label: "History" },
                            { icon: "⚙", label: "Settings" },
                            { icon: "ⓘ", label: "About" }
                        ]
                    }

                    Item { Layout.fillHeight: true }

                    Pill {
                        visible: Bridge.privateMode
                        text: "private mode"
                        icon: "●"
                        tint: Theme.accent
                        filled: true
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "v" + Bridge.version
                        color: Theme.textFaint
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontMicro
                    }
                }
            }

            // Content ------------------------------------------------------

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: Theme.gapLoose
                currentIndex: nav.currentIndex

                StatusScreen {}
                ChatboxScreen {}
                IntegrationsScreen {}
                HistoryScreen {}
                SettingsScreen {}
                AboutScreen {}
            }
        }
    }
}
