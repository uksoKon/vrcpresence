pragma Singleton
import VrcPresence
import QtQuick

QtObject {
    id: theme

    // Raw palette from the desktop (Serpantinum / matugen), or the built-in
    // fallback. Everything below is derived from these, so a theme switch on
    // the desktop restyles the whole app with no restart.
    readonly property color baseColor: Bridge.themeBase
    readonly property color mantleColor: Bridge.themeMantle
    readonly property color surfaceColor: Bridge.themeSurface
    readonly property color surfaceAltColor: Bridge.themeSurfaceAlt
    readonly property color borderColor: Bridge.themeBorder

    function withAlpha(c, a) {
        return Qt.rgba(c.r, c.g, c.b, a);
    }

    readonly property color background: withAlpha(baseColor, 0.84)
    readonly property color sidebar: withAlpha(mantleColor, 0.66)
    readonly property color surface: withAlpha(surfaceColor, 0.70)
    readonly property color surfaceAlt: withAlpha(surfaceAltColor, 0.78)
    readonly property color border: withAlpha(borderColor, 0.55)

    readonly property color accent: Bridge.themeAccent
    readonly property color accentSoft: withAlpha(accent, 0.20)
    readonly property color accentMuted: withAlpha(accent, 0.65)
    readonly property color accentText: baseColor

    readonly property color text: Bridge.themeText
    readonly property color textDim: Bridge.themeSubtext
    readonly property color textFaint: Bridge.themeFaint
    readonly property color good: Bridge.themeGood
    readonly property color warn: Bridge.themeWarn
    readonly property color bad: Bridge.themeBad

    readonly property int radiusCard: Bridge.themeRadius
    readonly property int radiusSmall: Math.max(4, Math.round(Bridge.themeRadius * 0.55))
    readonly property int radiusPill: 999

    readonly property int gapTight: 8
    readonly property int gap: 14
    readonly property int gapLoose: 20

    readonly property string fontMono: Bridge.themeFont
    readonly property int fontMicro: 11
    readonly property int fontSmall: 12
    readonly property int fontBody: 13
    readonly property int fontLead: 16
    readonly property int fontTitle: 20
    readonly property int fontHero: 26

    readonly property int animFast: 120
    readonly property int animBase: 200

    readonly property int sidebarWidth: 196
    readonly property int rowHeight: 38
}
