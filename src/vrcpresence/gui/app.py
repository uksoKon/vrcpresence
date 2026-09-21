from __future__ import annotations

import sys
from pathlib import Path

from ..config import Config
from ..engine import Engine


def run_gui() -> int:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance

    from .bridge import Bridge

    app = QGuiApplication(sys.argv)
    app.setApplicationName("vrcpresence")
    app.setOrganizationName("vrcpresence")

    engine = Engine(Config.load())
    bridge = Bridge(engine)

    # A registered singleton rather than a context property: the QML lives in a
    # directory with a qmldir, which makes it a module, and module types do not
    # see context properties.
    qmlRegisterSingletonInstance(Bridge, "VrcPresence", 1, 0, "Bridge", bridge)

    qml_engine = QQmlApplicationEngine()
    qml_dir = Path(__file__).parent / "qml"
    qml_engine.addImportPath(str(qml_dir))
    qml_engine.load(QUrl.fromLocalFile(str(qml_dir / "Main.qml")))

    if not qml_engine.rootObjects():
        print("error: failed to load the interface", file=sys.stderr)
        bridge.shutdown()
        return 1

    app.aboutToQuit.connect(bridge.shutdown)
    return app.exec()
