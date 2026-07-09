# GUI Control Center Design

## Goal

Replace the console-first recorder workflow with a polished Windows GUI while keeping the existing Python and FFmpeg recording backend.

## Direction

The selected direction is **Control Center**: one main window that shows recording state, area selection, audio status, start/stop control, and recent recordings. The app should feel quiet and utilitarian rather than decorative.

## Main Window

The main window contains:

- Recording status: Ready, Selecting area, Recording, Finalizing, Error.
- A large Start/Stop button.
- A recording timer.
- Current capture area summary: not selected, full screen-sized region, or explicit width/height and coordinates.
- Buttons for Select Area and Open Recordings Folder.
- Toggles for System audio, Microphone, and Show cursor.
- Audio readiness indicators for system audio and microphone.
- Last recordings list with Open and Show in folder actions.

## Recording Flow

1. The user launches `RecordScreen.bat`.
2. The GUI opens instead of a console-first workflow.
3. The app checks local FFmpeg and Python dependencies through the existing launcher.
4. The user can press Start or `Ctrl+Alt+Shift+R`.
5. If no region is selected, the app opens the existing region-selection overlay.
6. The app minimizes itself while selecting and recording so it does not appear in the captured video.
7. Recording starts after area selection.
8. Pressing Stop or `Ctrl+Alt+Shift+R` stops recording and returns the main window.
9. The finished MP4 appears in Last recordings.

## Hotkeys

`Ctrl+Alt+Shift+R` remains the global hotkey:

- If idle, it starts the same flow as the Start button.
- If recording, it stops the recording.

## Settings

First GUI version keeps settings simple:

- System audio: enabled by default.
- Microphone: enabled by default.
- Show cursor: enabled by default.

The backend must accept these options without requiring a rewrite. If an audio source is disabled, final muxing should include only the enabled audio source or no audio if both are disabled.

## Error Handling

User-facing errors should appear in the GUI status area and a compact details panel. The app should show clear messages for:

- FFmpeg download or discovery failure.
- Microphone access denied.
- System loopback unavailable.
- Region selection canceled.
- FFmpeg capture failure.
- Final muxing failure.

The full FFmpeg log should remain available in the recordings folder for diagnostics.

## Architecture

Keep the current backend modules:

- `screen_recorder/recorder.py` remains responsible for video capture, audio capture integration, stop, and muxing.
- `screen_recorder/selection.py` remains responsible for region selection.
- `screen_recorder/ffmpeg_manager.py` remains responsible for local FFmpeg.
- `screen_recorder/audio.py` remains responsible for microphone and system-audio capture.

Add a GUI layer:

- `screen_recorder/gui.py`: main Tkinter GUI and state transitions.
- `screen_recorder/app.py`: route startup to GUI by default, keeping a CLI/help entry point.

Tkinter is acceptable for this first GUI version because it is already in use for region selection and adds no new heavy runtime.

## Testing

Tests should cover:

- GUI-independent state transitions where possible.
- Start flow calls region selection when no region is selected.
- Hotkey start/stop maps to the same commands as GUI buttons.
- Recorder command construction respects system audio, microphone, and cursor toggles.
- Launcher still starts and `--help` remains quiet.

Manual verification should cover:

- Launch GUI from `RecordScreen.bat`.
- Select full screen and confirm captured area matches the screen under Windows scaling.
- Start and stop from GUI.
- Start and stop from `Ctrl+Alt+Shift+R`.
- Confirm the GUI does not appear in the recording.
- Open last recording from the GUI.
