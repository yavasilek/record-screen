# Screen Recorder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Windows screen recorder with region selection, global hotkey control, local FFmpeg, and mixed system plus microphone audio.

**Architecture:** A small Python package handles UI, audio capture, and lifecycle while FFmpeg handles desktop video capture and final muxing. The launcher creates a local virtual environment, installs Python dependencies, and starts the app.

**Tech Stack:** Python 3, Tkinter, keyboard, soundcard, numpy, pytest, FFmpeg gdigrab.

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `screen_recorder/__init__.py`
- Create: `screen_recorder/config.py`
- Create: `tests/test_config.py`

- [ ] Write a failing test for default paths and recording settings.
- [ ] Implement config constants and path helpers.
- [ ] Run `python -m pytest tests/test_config.py -v`.

### Task 2: FFmpeg Management

**Files:**
- Create: `screen_recorder/ffmpeg_manager.py`
- Create: `tests/test_ffmpeg_manager.py`

- [ ] Write failing tests for local FFmpeg path resolution.
- [ ] Implement local path discovery and portable ZIP download/extract logic.
- [ ] Run `python -m pytest tests/test_ffmpeg_manager.py -v`.

### Task 3: Region Selection Model

**Files:**
- Create: `screen_recorder/selection.py`
- Create: `tests/test_selection.py`

- [ ] Write failing tests for rectangle normalization and minimum-size validation.
- [ ] Implement the testable rectangle helpers.
- [ ] Implement the Tkinter full-screen selection overlay.
- [ ] Run `python -m pytest tests/test_selection.py -v`.

### Task 4: Recorder Command and Process

**Files:**
- Create: `screen_recorder/recorder.py`
- Create: `tests/test_recorder.py`

- [ ] Write failing tests for FFmpeg command construction.
- [ ] Implement command building for gdigrab video capture and final video/audio muxing.
- [ ] Implement process start, graceful stop, and status checks.
- [ ] Run `python -m pytest tests/test_recorder.py -v`.

### Task 5: Microphone Access Probe

**Files:**
- Create: `screen_recorder/audio.py`
- Create: `tests/test_audio.py`

- [ ] Write failing tests for permission guidance, WASAPI loopback selection, and PCM conversion.
- [ ] Implement microphone/system audio probes and WAV capture through `soundcard`.
- [ ] Run `python -m pytest tests/test_audio.py -v`.

### Task 6: Console App and Launcher

**Files:**
- Create: `screen_recorder/app.py`
- Create: `RecordScreen.bat`

- [ ] Implement startup, dependency flow, hotkey toggle, Ctrl+C cleanup, and user-facing console messages.
- [ ] Implement the Windows launcher that creates `.venv`, installs requirements, and runs the app.
- [ ] Run `python -m pytest -v`.
- [ ] Run `python -m screen_recorder.app --help`.
