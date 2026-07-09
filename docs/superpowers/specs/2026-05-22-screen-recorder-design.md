# Screen Recorder Design

## Goal

Build a small Windows screen recorder that starts and stops with `Ctrl+Alt+Shift+R`, lets the user select a desktop region before recording, and records both computer audio and microphone audio.

## User Flow

1. The user launches the program with `RecordScreen.bat`.
2. The console app starts and listens for `Ctrl+Alt+Shift+R`.
3. When the hotkey is pressed and no recording is active, a translucent full-screen overlay appears.
4. The user drags a rectangle over any desktop area. This captures the desktop pixels inside that rectangle, not a single selected application.
5. Releasing the mouse starts recording immediately.
6. Pressing `Ctrl+Alt+Shift+R` again stops the recording.
7. Pressing `Esc` while selecting cancels the selection.
8. Pressing `Ctrl+C` stops any active recording and exits.

## Output

Recordings are saved as `recordings/screen_YYYY-MM-DD_HH-MM-SS.mp4`.

## Architecture

The Python app owns the hotkey, region-selection overlay, local FFmpeg installation, audio capture, microphone access check, and process lifecycle. FFmpeg performs desktop capture through `gdigrab`. Python captures system audio through WASAPI loopback and microphone audio through the default input device using `soundcard`, writes temporary WAV files, and then local FFmpeg muxes the video plus mixed audio into one MP4.

## Components

- `screen_recorder/config.py`: paths and recording defaults.
- `screen_recorder/ffmpeg_manager.py`: locate or download local FFmpeg.
- `screen_recorder/audio.py`: microphone/system-audio probes, WASAPI loopback selection, and WAV capture.
- `screen_recorder/selection.py`: Tkinter overlay for region selection.
- `screen_recorder/recorder.py`: build/manage the FFmpeg video process and final mux step.
- `screen_recorder/app.py`: console app and hotkey lifecycle.

## Error Handling

If FFmpeg is missing, the app downloads a portable Windows build into `tools/ffmpeg`. If microphone access fails, the app prints Windows privacy-setting instructions and refuses to start recording. If system audio loopback is unavailable, the app reports that before selection starts. If FFmpeg exits early, the app reports stderr so the user can see the capture problem.

## Testing

Unit tests cover command construction, FFmpeg path discovery, rectangle normalization, and microphone guidance text. Manual verification covers startup, region selection, hotkey toggling, and a short recording.
