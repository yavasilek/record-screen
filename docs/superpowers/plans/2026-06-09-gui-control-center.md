# GUI Control Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished Tkinter Control Center GUI for the existing Windows screen recorder.

**Architecture:** Keep FFmpeg, audio capture, and region selection in the current backend. Add recorder options for cursor/audio toggles, add a Tkinter GUI shell, and make `RecordScreen.bat` launch the GUI through `pythonw.exe` while preserving console help mode.

**Tech Stack:** Python 3, Tkinter/ttk, keyboard, soundcard, numpy, FFmpeg, pytest.

---

### Task 1: Backend Recording Options

**Files:**
- Modify: `screen_recorder/recorder.py`
- Modify: `screen_recorder/audio.py`
- Modify: `tests/test_recorder.py`

- [ ] **Step 1: Write failing tests**

```python
def test_video_capture_command_can_hide_cursor():
    command = build_video_capture_command(Path("ffmpeg.exe"), Region(0, 0, 640, 360), Path("out.video.mp4"), show_cursor=False)
    assert command[command.index("-draw_mouse") + 1] == "0"

def test_mux_command_supports_video_only_output():
    command = build_mux_command(Path("ffmpeg.exe"), Path("out.video.mp4"), None, None, Path("out.mp4"))
    assert command.count("-i") == 1
    assert "-filter_complex" not in command
```

- [ ] **Step 2: Run failing tests**

Run: `python -m pytest tests/test_recorder.py -v`

- [ ] **Step 3: Implement options**

Add `RecordingOptions(show_cursor=True, system_audio=True, microphone=True)`. Make video command use `show_cursor`. Make mux support two audio tracks, one audio track, or no audio.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_recorder.py -v`

### Task 2: GUI State Helpers

**Files:**
- Create: `screen_recorder/gui.py`
- Create: `tests/test_gui.py`

- [ ] **Step 1: Write failing tests**

```python
def test_format_region_summary_shows_dimensions_and_origin():
    assert format_region_summary(Region(10, 20, 640, 360)) == "640 x 360 at 10,20"

def test_recent_recordings_returns_newest_mp4_first(tmp_path):
    older = tmp_path / "older.mp4"; older.write_text("")
    newer = tmp_path / "newer.mp4"; newer.write_text("")
    assert recent_recordings(tmp_path, limit=2)[0] == newer
```

- [ ] **Step 2: Run failing tests**

Run: `python -m pytest tests/test_gui.py -v`

- [ ] **Step 3: Implement GUI helpers**

Implement `format_region_summary`, `recent_recordings`, and a `RecorderGui` class skeleton with no side effects during import.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_gui.py -v`

### Task 3: Control Center GUI

**Files:**
- Modify: `screen_recorder/gui.py`
- Modify: `screen_recorder/app.py`
- Modify: `tests/test_app.py`

- [ ] **Step 1: Write failing startup tests**

```python
def test_main_launches_gui_by_default(monkeypatch):
    events = []
    monkeypatch.setattr(app_module, "ScreenRecorderGui", lambda: SimpleNamespace(run=lambda: events.append("gui") or 0))
    assert app_module.main([]) == 0
    assert events == ["gui"]
```

- [ ] **Step 2: Run failing tests**

Run: `python -m pytest tests/test_app.py -v`

- [ ] **Step 3: Implement GUI**

Build the Tkinter window with status, Start/Stop, Select Area, timer, capture area summary, toggles, audio indicators, last recordings, Open and Show in folder actions. Keep hotkey behavior through `keyboard.add_hotkey`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_app.py tests/test_gui.py -v`

### Task 4: Launcher Without Console Noise

**Files:**
- Modify: `RecordScreen.ps1`
- Modify: `README.md`
- Modify: `tests/test_launcher.py`

- [ ] **Step 1: Write/update launcher test**

Ensure `RecordScreen.bat --help` still prints help and no pip noise.

- [ ] **Step 2: Implement launcher**

Use `.venv\Scripts\pythonw.exe` for normal GUI startup. Use `.venv\Scripts\python.exe` when arguments are supplied, so `--help` remains visible.

- [ ] **Step 3: Run full verification**

Run:

```powershell
python -m pytest -v
cmd /c RecordScreen.bat --help
python -m screen_recorder.app --help
```

Expected: tests pass, help prints cleanly, no `Requirement already satisfied` lines.
