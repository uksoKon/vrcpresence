import VrcPresence
import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

ColumnLayout {
    spacing: Theme.gap

    // Hero ---------------------------------------------------------------

    Card {
        Layout.fillWidth: true
        Layout.fillHeight: false
        Layout.preferredHeight: 150
        Layout.maximumHeight: 150
        padding: Theme.gap
        highlighted: Bridge.inWorld

        RowLayout {
            anchors.fill: parent
            spacing: Theme.gapLoose

            Rectangle {
                Layout.preferredWidth: 118
                Layout.preferredHeight: 118
                Layout.alignment: Qt.AlignVCenter
                radius: Theme.radiusCard
                color: Theme.surfaceAlt
                border.width: 1
                border.color: Theme.border
                clip: true

                Image {
                    anchors.fill: parent
                    source: Bridge.worldImageUrl
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    visible: Bridge.worldImageUrl !== "" && status === Image.Ready
                }

                Text {
                    anchors.centerIn: parent
                    visible: Bridge.worldImageUrl === ""
                    text: Bridge.vrchatRunning ? "◌" : "⏻"
                    color: Theme.textFaint
                    font.pixelSize: 30
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Theme.gapTight

                Item { Layout.fillHeight: true }

                Text {
                    Layout.fillWidth: true
                    text: Bridge.headline
                    color: Bridge.inWorld ? Theme.text : Theme.textDim
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontHero
                    elide: Text.ElideRight
                }

                Text {
                    Layout.fillWidth: true
                    text: Bridge.subheadline
                    color: Theme.textFaint
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.fontSmall
                    elide: Text.ElideRight
                    visible: text !== ""
                }

                RowLayout {
                    spacing: Theme.gapTight
                    visible: Bridge.inWorld

                    Pill {
                        text: Bridge.worldCapacity > 0
                            ? Bridge.playerCount + " / " + Bridge.worldCapacity
                            : Bridge.playerCount + (Bridge.playerCount === 1 ? " player" : " players")
                        icon: "◉"
                        tint: Theme.accent
                        filled: true
                    }

                    Pill {
                        visible: Bridge.mode !== ""
                        text: Bridge.mode
                        icon: Bridge.mode === "VR" ? "⬛" : "▭"
                        tint: Theme.accentMuted
                    }

                    Pill {
                        visible: Bridge.sessionTime !== ""
                        text: Bridge.sessionTime
                        icon: "◴"
                        tint: Theme.textDim
                    }

                    Pill {
                        visible: Bridge.instanceType !== ""
                        text: Bridge.instanceType
                        tint: Theme.textDim
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // Stat row -------------------------------------------------------------

    RowLayout {
        Layout.fillWidth: true
        // Nested layouts default to fillHeight: true, which stretches these
        // tiles into full-height columns. Pin the height explicitly.
        Layout.fillHeight: false
        Layout.preferredHeight: 60
        Layout.maximumHeight: 60
        spacing: Theme.gapTight

        StatTile {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "vrchat"
            value: Bridge.vrchatRunning ? "running" : "closed"
            valueColor: Bridge.vrchatRunning ? Theme.good : Theme.textFaint
        }

        StatTile {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "discord"
            value: Bridge.discordStatus
            valueColor: Bridge.discordReady ? Theme.good
                : (Bridge.discordStatus === "needs app id" ? Theme.warn : Theme.textFaint)
        }

        StatTile {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "world api"
            value: Bridge.vrchatAuthenticated ? "linked" : "not linked"
            valueColor: Bridge.vrchatAuthenticated ? Theme.good : Theme.textFaint
        }

        StatTile {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "today"
            value: Bridge.todaySummary
        }
    }

    // Players + recent ------------------------------------------------------

    // Offline: one calm panel instead of two empty columns ------------------

    Card {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !Bridge.vrchatRunning
        padding: Theme.gapLoose

        ColumnLayout {
            anchors.centerIn: parent
            width: parent.width * 0.8
            spacing: Theme.gapTight

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "◌"
                color: Theme.textFaint
                font.pixelSize: 34
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Waiting for VRChat"
                color: Theme.textDim
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontLead
            }

            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: Bridge.logFound
                    ? "Your world, instance and headset mode appear here the moment you launch it."
                    : "No VRChat log found yet. It appears after VRChat runs once."
                color: Theme.textFaint
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontSmall
            }

            Pill {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: Theme.gapTight
                visible: Bridge.sessionHistoryOnly
                text: "session-only history"
                icon: "●"
                tint: Theme.textFaint
            }
        }
    }

    // Online: players and recent worlds --------------------------------------

    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: Bridge.vrchatRunning
        spacing: Theme.gapTight

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            padding: Theme.gap

            ColumnLayout {
                anchors.fill: parent
                spacing: Theme.gapTight

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: "In this instance"
                        color: Theme.textFaint
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontMicro
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: Bridge.playerCount
                        color: Theme.accent
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontMicro
                    }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: Bridge.players
                    spacing: 1

                    delegate: Rectangle {
                        required property string modelData
                        width: ListView.view.width
                        height: 26
                        radius: Theme.radiusSmall
                        color: hover.hovered ? Theme.surfaceAlt : "transparent"

                        HoverHandler { id: hover }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.leftMargin: Theme.gapTight
                            text: modelData
                            color: Theme.text
                            font.family: Theme.fontMono
                            font.pixelSize: Theme.fontSmall
                            elide: Text.ElideRight
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: parent.count === 0
                        text: Bridge.vrchatRunning ? "Nobody here yet" : "Not in a session"
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
                    text: "Recent worlds"
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

                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 26
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
                                text: modelData.duration
                                color: Theme.textFaint
                                font.family: Theme.fontMono
                                font.pixelSize: Theme.fontMicro
                            }
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: parent.count === 0
                        text: "Nothing yet"
                        color: Theme.textFaint
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.fontSmall
                    }
                }
            }
        }
    }
}
