import VrcPresence
import QtQuick

SettingSwitch {
    id: control

    // Binds straight to Bridge.options[key] instead of one hand-written
    // property per setting - there are ~20 of these on the Integrations
    // screen alone.
    property string key: ""

    checked: Bridge.options[key] === true
    onToggled: (v) => Bridge.setOption(key, v)

    Connections {
        target: Bridge
        function onChanged() {
            control.checked = Bridge.options[control.key] === true;
        }
    }
}
