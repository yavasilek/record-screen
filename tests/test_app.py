from pathlib import Path

import screen_recorder.app as app_module
from screen_recorder.app import RecorderApp
from screen_recorder.selection import Region


class FakeRecorder:
    def __init__(self) -> None:
        self.ffmpeg_path = Path("ffmpeg.exe")
        self.is_recording = False

    def start(self, region: Region, output_path: Path) -> Path:
        self.is_recording = True
        return output_path

    def stop(self) -> Path:
        self.is_recording = False
        return Path("recordings/out.mp4")


def test_main_enables_dpi_awareness_before_launching_gui(monkeypatch):
    events: list[str] = []

    class FakeGui:
        def run(self) -> int:
            events.append("gui")
            return 0

    monkeypatch.setattr(app_module, "enable_dpi_awareness", lambda: events.append("dpi"), raising=False)
    monkeypatch.setattr(app_module, "RecorderGui", FakeGui, raising=False)

    assert app_module.main([]) == 0
    assert events == ["dpi", "gui"]


def test_main_can_launch_console_mode(monkeypatch):
    events: list[str] = []

    class FakeConsoleApp:
        def run(self) -> int:
            events.append("console")
            return 0

    monkeypatch.setattr(app_module, "enable_dpi_awareness", lambda: None, raising=False)
    monkeypatch.setattr(app_module, "RecorderApp", FakeConsoleApp)

    assert app_module.main(["--console"]) == 0
    assert events == ["console"]


def test_start_minimizes_console_before_selection_and_keeps_it_hidden(monkeypatch, tmp_path):
    events: list[str] = []
    fake_recorder = FakeRecorder()
    selected_region = Region(x=0, y=0, width=100, height=100)

    monkeypatch.setattr(app_module, "verify_microphone_access", lambda: events.append("mic"))
    monkeypatch.setattr(app_module, "verify_system_audio_access", lambda: events.append("system"))
    monkeypatch.setattr(app_module, "minimize_console", lambda: events.append("minimize"), raising=False)
    monkeypatch.setattr(app_module, "restore_console", lambda: events.append("restore"), raising=False)
    monkeypatch.setattr(app_module, "select_region", lambda: events.append("select") or selected_region)
    monkeypatch.setattr(app_module, "build_output_path", lambda: tmp_path / "out.mp4")

    recorder_app = RecorderApp()
    recorder_app.recorder = fake_recorder
    recorder_app._toggle_recording()

    assert events == ["mic", "system", "minimize", "select"]
    assert fake_recorder.is_recording


def test_stop_restores_console(monkeypatch):
    events: list[str] = []
    fake_recorder = FakeRecorder()
    fake_recorder.is_recording = True

    monkeypatch.setattr(app_module, "restore_console", lambda: events.append("restore"), raising=False)

    recorder_app = RecorderApp()
    recorder_app.recorder = fake_recorder
    recorder_app._stop_recording()

    assert events == ["restore"]
    assert not fake_recorder.is_recording
