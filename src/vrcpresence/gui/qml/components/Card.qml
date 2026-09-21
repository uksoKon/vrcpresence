import QtQuick
import ".."

Rectangle {
    default property alias content: inner.data
    property int padding: Theme.gapLoose
    property bool highlighted: false

    color: Theme.surface
    radius: Theme.radiusCard
    border.width: 1
    border.color: highlighted ? Theme.accent : Theme.border

    Behavior on border.color {
        ColorAnimation { duration: Theme.animBase }
    }

    Item {
        id: inner
        anchors.fill: parent
        anchors.margins: parent.padding
    }
}
