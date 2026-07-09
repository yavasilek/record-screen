# Record Screen

Windows screen recorder with a Control Center GUI, selectable capture area, system audio, microphone audio, and local FFmpeg.

## Run

Double-click `RecordScreen.bat`.

On normal startup, the launcher checks dependencies quietly and opens the GUI through `pythonw.exe`, so the console window does not stay on screen. If you run `RecordScreen.bat --help`, it uses console mode and prints help text.

## Controls

- `Start`: select an area if needed, then start recording.
- `Stop`: stop recording and finalize the MP4.
- `Select Area`: choose a desktop region before recording.
- `Ctrl+Alt+Shift+R`: global hotkey for Start/Stop.
- `System audio`: record computer audio.
- `Microphone`: record the default microphone.
- `Show cursor`: include the mouse cursor in the video.

Finished files are saved in `recordings`.

## Notes

The GUI hides itself while selecting and recording so it does not appear in the captured video.

If the selected area has an odd width or height, the recorder trims that dimension by 1 pixel for H.264 compatibility.

If microphone access fails, check:

`Windows Settings -> Privacy & security -> Microphone -> Allow desktop apps to access your microphone`.
