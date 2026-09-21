import json

from vrcpresence.theming import BUILT_IN, DEFAULT_FONT, load_desktop_theme


def write_settings(tmp_path, theme: dict):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": theme, "wallpaperDir": "/x"}))
    return path


def test_missing_file_falls_back_to_built_in(tmp_path):
    theme = load_desktop_theme(tmp_path / "nope.json")
    assert theme.color("mauve") == BUILT_IN["mauve"]
    assert theme.font_family == DEFAULT_FONT
    assert not theme.following_desktop


def test_reads_desktop_palette(tmp_path):
    path = write_settings(
        tmp_path,
        {
            "colors": {"base": "#101010", "mauve": "#ff00ff", "text": "#ffffff"},
            "fontFamily": "Maple Mono SemiBold",
            "borderRadius": 18,
            "activePreset": "Matugen",
        },
    )
    theme = load_desktop_theme(path)

    assert theme.color("base") == "#101010"
    assert theme.color("mauve") == "#ff00ff"
    assert theme.font_family == "Maple Mono SemiBold"
    assert theme.radius == 18
    assert theme.preset == "Matugen"
    assert theme.following_desktop


def test_partial_palette_keeps_built_in_for_missing_keys(tmp_path):
    path = write_settings(tmp_path, {"colors": {"base": "#101010"}})
    theme = load_desktop_theme(path)

    assert theme.color("base") == "#101010"
    assert theme.color("green") == BUILT_IN["green"]


def test_radius_is_clamped(tmp_path):
    assert load_desktop_theme(write_settings(tmp_path, {"borderRadius": 99})).radius == 28
    assert load_desktop_theme(write_settings(tmp_path, {"borderRadius": -5})).radius == 0


def test_malformed_file_is_survivable(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json")
    assert load_desktop_theme(path).color("mauve") == BUILT_IN["mauve"]


def test_non_color_values_are_ignored(tmp_path):
    path = write_settings(tmp_path, {"colors": {"mauve": "notacolor", "base": 42}})
    theme = load_desktop_theme(path)
    assert theme.color("mauve") == BUILT_IN["mauve"]
    assert theme.color("base") == BUILT_IN["base"]
