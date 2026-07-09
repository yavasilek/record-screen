import os

from screen_recorder.gui import (
    DETAILS_TEXT_VISIBLE_ROWS,
    GuiState,
    RecorderStatus,
    RECORDINGS_LIST_VISIBLE_ROWS,
    RECORDINGS_PANEL_MIN_WIDTH,
    WINDOW_GEOMETRY,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    format_region_summary,
    recent_recordings,
)
from screen_recorder.selection import Region


def test_format_region_summary_handles_missing_region():
    assert format_region_summary(None) == "Область не выбрана"


def test_format_region_summary_shows_dimensions_and_origin():
    assert format_region_summary(Region(x=10, y=20, width=640, height=360)) == "640 x 360, координаты 10,20"


def test_recent_recordings_returns_newest_mp4_first(tmp_path):
    older = tmp_path / "older.mp4"
    newer = tmp_path / "newer.mp4"
    older.write_text("", encoding="utf-8")
    newer.write_text("", encoding="utf-8")
    os.utime(older, (100, 100))
    os.utime(newer, (200, 200))

    assert recent_recordings(tmp_path, limit=2)[0] == newer
    assert older in recent_recordings(tmp_path, limit=2)


def test_gui_state_defaults_to_ready_with_audio_enabled():
    state = GuiState()

    assert state.status is RecorderStatus.READY
    assert state.system_audio
    assert state.microphone
    assert state.show_cursor


def test_gui_layout_keeps_recordings_panel_readable():
    assert WINDOW_MIN_WIDTH >= 820
    assert RECORDINGS_PANEL_MIN_WIDTH >= 240


def test_gui_layout_stays_compact_for_scaled_displays():
    _, height = WINDOW_GEOMETRY.split("x", maxsplit=1)

    assert int(height) <= 540
    assert WINDOW_MIN_HEIGHT <= 520
    assert RECORDINGS_LIST_VISIBLE_ROWS <= 7
    assert DETAILS_TEXT_VISIBLE_ROWS <= 3
