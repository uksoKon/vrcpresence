"""Keeps the test suite out of the real user's config and data directories.

Without this, running the tests writes fixture worlds into the history
database of whoever is running them.
"""

import pytest


@pytest.fixture(autouse=True)
def isolate_user_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr("vrcpresence.config.config_dir", lambda: tmp_path / "config")
    monkeypatch.setattr("vrcpresence.config.data_dir", lambda: tmp_path / "data")
    monkeypatch.setattr("vrcpresence.engine.config_dir", lambda: tmp_path / "config")
    monkeypatch.setattr("vrcpresence.engine.data_dir", lambda: tmp_path / "data")
