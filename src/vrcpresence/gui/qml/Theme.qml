pragma Singleton
import QtQuick

QtObject {
    readonly property color background: "#0d0f14"
    readonly property color surface: "#151822"
    readonly property color surfaceAlt: "#1b1f2b"
    readonly property color border: "#252a38"

    readonly property color accent: "#b36ce8"
    readonly property color accentMuted: "#6d4a8f"
    readonly property color accentText: "#120b18"

    readonly property color text: "#e4e6ee"
    readonly property color textDim: "#8b91a4"
    readonly property color good: "#7ddba0"
    readonly property color bad: "#e8737d"

    readonly property int radiusSmall: 8
    readonly property int radiusCard: 16
    readonly property int radiusPill: 999

    readonly property int gapTight: 8
    readonly property int gap: 14
    readonly property int gapLoose: 22

    readonly property string fontMono: "monospace"
    readonly property int fontSmall: 12
    readonly property int fontBody: 13
    readonly property int fontTitle: 20
    readonly property int fontHero: 28

    readonly property int animFast: 120
    readonly property int animBase: 200
}
