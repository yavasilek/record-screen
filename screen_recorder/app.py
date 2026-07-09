from __future__ import annotations

import argparse
import queue
import sys
import threading
import time

from .audio import AudioCaptureError, MicrophoneAccessError, verify_microphone_access, verify_system_audio_access
from .config import HOTKEY
from .ffmpeg_manager import ensure_ffmpeg
from .recorder import ScreenRecorder, build_output_path
from .selection import select_region
from .windows import enable_dpi_awareness, minimize_console, restore_console
from .gui import RecorderGui


class RecorderApp:
    def __init__(self) -> None:
        self.actions: queue.Queue[str] = queue.Queue()
        self.stop_event = threading.Event()
        self.recorder: ScreenRecorder | None = None

    def run(self) -> int:
        import keyboard

        ffmpeg_path = ensure_ffmpeg()
        self.recorder = ScreenRecorder(ffmpeg_path)

        keyboard.add_hotkey(HOTKEY, lambda: self.actions.put("toggle"))
        print("Screen Recorder is running.")
        print(f"Hotkey: {HOTKEY}")
        print("First press selects a region and starts recording; second press stops it.")
        print("Use Ctrl+C in this window to exit.")

        try:
            while not self.stop_event.is_set():
                self._handle_next_action()
                self._report_ffmpeg_exit()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            keyboard.unhook_all_hotkeys()
            self._stop_recording()
            restore_console()
        return 0

    def _handle_next_action(self) -> None:
        try:
            action = self.actions.get(timeout=0.2)
        except queue.Empty:
            return

        if action == "toggle":
            self._toggle_recording()

    def _toggle_recording(self) -> None:
        if self.recorder is None:
            return

        if self.recorder.is_recording:
            self._stop_recording()
            return

        print("Checking microphone access...")
        try:
            verify_microphone_access()
        except MicrophoneAccessError as error:
            print(error)
            return

        print("Checking system audio access...")
        try:
            verify_system_audio_access()
        except AudioCaptureError as error:
            print(error)
            return

        print("Select a region with the mouse. Esc cancels selection.")
        minimize_console()
        try:
            region = select_region()
        except Exception:
            restore_console()
            raise
        if region is None:
            restore_console()
            print("Selection canceled.")
            return

        output_path = build_output_path()
        try:
            self.recorder.start(region, output_path)
        except Exception:
            restore_console()
            raise
        print(f"Recording started: {output_path}")

    def _stop_recording(self) -> None:
        if self.recorder is None or not self.recorder.is_recording:
            return

        try:
            output_path = self.recorder.stop()
        finally:
            restore_console()
        if output_path is not None:
            print(f"Recording stopped: {output_path}")

    def _report_ffmpeg_exit(self) -> None:
        if self.recorder is None:
            return

        error = self.recorder.poll_error()
        if error is None:
            return

        restore_console()
        print("FFmpeg stopped before recording finished:")
        print(error)
        self.recorder.process = None
        time.sleep(0.2)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="record-screen",
        description="Record a selected desktop region with system audio and microphone audio.",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Run the legacy console hotkey workflow instead of the GUI.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    enable_dpi_awareness()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.console:
        return RecorderApp().run()
    return RecorderGui().run()


if __name__ == "__main__":
    raise SystemExit(main())
