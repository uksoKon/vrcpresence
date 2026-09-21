import VrcPresence
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

ColumnLayout {
    spacing: Theme.gap

    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: false
        Layout.preferredHeight: 60
        Layout.maximumHeight: 60
        spacing: Theme.gapTight

        Repeater {
            model: Bridge.historyTotals

            StatTile {
                required property var modelData
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: modelData.label
                value: modelData.value
                valueColor: Theme.accent
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: Theme.gapTight

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 2
            padding: Theme.gap

            ColumnLayout {
                anchors.fill: parent
                spacing: Theme.gapTight

                Text {
                    text: "Worlds visited"
                    color: Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: Bridge.visits
                    spacing: 1
                    ScrollBar.vertical: ScrollBar {}

                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 30
                        radius: Theme.radiusSmall
                        color: hover.hovered ? Theme.surfaceAlt : "transparent"

                        HoverHandler { id: hover }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Theme.gapTight
                            anchors.rightMargin: Theme.gapTight
                            spacing: Theme.gap

                            Text {
                                Layout.preferredWidth: 104
                                text: modelData.when
                                color: Theme.textFaint
                                font.family: Theme.fontMono
                                font.pixelSize: Theme.fontMicro
                            }

                            Text {
                                Layout.fillWidth: true
                                text: modelData.name
                                color: Theme.text
                                font.family: Theme.fontMono
                                font.pixelSize: Theme.fontSmall
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.preferredWidth: 44
                                horizontalAlignment: Text.AlignRight
                                text: modelData.duration
                                color: Theme.textDim
                                font.family: Theme.fontMono
                                font.pixelSize: Theme.fontMicro
                            }

                            Text {
                                Layout.preferredWidth: 52
                                horizontalAlignment: Text.AlignRight
                                text: "peak " + modelData.peak
                                color: Theme.textFaint
                                font.family: Theme.fontMono
                                font.pixelSize: Theme.fontMicro
                            }
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: parent.count === 0
                        text: "No worlds recorded yet"
                        color: Theme.textFaint
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontSmall
                    }
                }
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            padding: Theme.gap

            ColumnLayout {
                anchors.fill: parent
                spacing: Theme.gapTight

                Text {
                    text: "People you run into"
                    color: Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontMicro
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: Bridge.peopleMet
                    spacing: 1
                    ScrollBar.vertical: ScrollBar {}

                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 30
                        radius: Theme.radiusSmall
                        color: hover.hovered ? Theme.surfaceAlt : "transparent"

                        HoverHandler { id: hover }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Theme.gapTight
                            anchors.rightMargin: Theme.gapTight
                            spacing: Theme.gapTight

                            Text {
                                Layout.fillWidth: true
                                text: modelData.name
                                color: Theme.text
                                font.family: Theme.fontMono
                                font.pixelSize: Theme.fontSmall
                                elide: Text.ElideRight
                            }

                            Text {
                                text: modelData.shared
                                color: Theme.accent
                                font.family: Theme.fontMono
                                font.pixelSize: Theme.fontMicro
                            }
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: parent.count === 0
                        text: "Nobody yet"
                        color: Theme.textFaint
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontSmall
                    }
                }
            }
        }
    }
}
