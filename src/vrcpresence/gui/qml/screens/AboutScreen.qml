import VrcPresence
import QtQuick
import ".."
import "../components"

Item {
    Column {
        anchors.centerIn: parent
        spacing: Theme.gap
        width: parent.width * 0.8

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "◉"
            color: Theme.accent
            font.pixelSize: 64
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Theme.gapTight

            Text {
                text: "vrcpresence"
                color: Theme.text
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontHero
                anchors.bottom: parent.bottom
            }

            Text {
                text: "v" + Bridge.version
                color: Theme.textDim
                font.family: Theme.fontMono
                font.pixelSize: Theme.fontSmall
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 6
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "VRChat status, Discord presence and chatbox for Linux"
            color: Theme.textDim
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontBody
        }

        Item { width: 1; height: Theme.gap }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: "World, players and headset mode are read from VRChat's own log - "
                + "OSC cannot provide them. If your status ever goes blank after a "
                + "VRChat update, run  vrcpresence calibrate  to see what the parser is missing."
            color: Theme.textDim
            font.family: Theme.fontMono
            font.pixelSize: Theme.fontSmall
            lineHeight: 1.3
        }
    }
}
