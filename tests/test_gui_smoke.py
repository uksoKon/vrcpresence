"""Loads the real QML tree and fails on any binding error.

A QML interface "loads" happily with every binding broken, so asserting the
root object exists proves almost nothing. This captures Qt's own warnings and
treats them as failures, which is what catches a renamed property or a
singleton that QML cannot see.
"""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance

from vrcpresence.config import Config
from vrcpresence.engine import Engine
from vrcpresence.gui.bridge import Bridge
from vrcpresence.log_watcher import LogWatcher

QML_DIR = Path(__file__).resolve().parents[1] / "src" / "vrcpresence" / "gui" / "qml"


@pytest.fixture(scope="module")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication([])
    yield app


def test_qml_loads_without_binding_errors(qt_app, tmp_path_factory):
    messages: list[str] = []

    def handler(mode, context, message):
        if mode in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(message)

    qInstallMessageHandler(handler)
    try:
        log_dir = tmp_path_factory.mktemp("logs")
        config = Config(
            discord_enabled=False,
            chatbox_enabled=False,
            notifications_enabled=False,
            history_enabled=False,
        )
        engine = Engine(config, log_watcher=LogWatcher(log_dir=log_dir))
        bridge = Bridge(engine)
        qmlRegisterSingletonInstance(Bridge, "VrcPresence", 1, 0, "Bridge", bridge)

        qml_engine = QQmlApplicationEngine()
        qml_engine.addImportPath(str(QML_DIR))
        qml_engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))

        assert qml_engine.rootObjects(), "Main.qml produced no root object"

        qt_app.processEvents()

        problems = [m for m in messages if "TypeError" in m or "unavailable" in m or "is not defined" in m]
        assert not problems, "QML binding errors:\n" + "\n".join(problems)

        bridge.shutdown()
        del qml_engine
    finally:
        qInstallMessageHandler(None)
