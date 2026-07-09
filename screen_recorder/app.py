from __future__ import annotations

import argparse
import queue
import sys
import threading
import time

from .audio import AudioCaptureError, MicrophoneAccessError, verify_microphone_access, verify_system_audio_access
from .ffmpeg_manager import ensure_ffmpeg
from .recorder import ScreenRecorder, build_output_path
from .selection import select_region
from .settings import load_settings
from .windows import enable_dpi_awareness, minimize_console, restore_console
from .gui import RecorderGui


class RecorderApp:
    def __init__(self) -> None:
        self.actions: queue.Queue[str] = queue.Queue()
        self.stop_event = threading.Event()
        self.recorder: ScreenRecorder | None = None

    def run(self) -> int:
        import keyboard

        settings = load_settings()
        ffmpeg_path = ensure_ffmpeg()
        self.recorder = ScreenRecorder(ffmpeg_path)

        keyboard.add_hotkey(settings.hotkey, lambda: self.actions.put("toggle"))
        print("Запись экрана запущена.")
        print(f"Горячая клавиша: {settings.hotkey}")
        print("Первое нажатие выбирает область и запускает запись, второе останавливает её.")
        print("Для выхода нажмите Ctrl+C в этом окне.")

        try:
            while not self.stop_event.is_set():
                self._handle_next_action()
                self._report_ffmpeg_exit()
        except KeyboardInterrupt:
            print("\nВыход...")
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

        print("Проверяю доступ к микрофону...")
        try:
            verify_microphone_access()
        except MicrophoneAccessError as error:
            print(error)
            return

        print("Проверяю доступ к системному звуку...")
        try:
            verify_system_audio_access()
        except AudioCaptureError as error:
            print(error)
            return

        print("Выберите область мышью. Esc отменяет выбор.")
        minimize_console()
        try:
            region = select_region()
        except Exception:
            restore_console()
            raise
        if region is None:
            restore_console()
            print("Выбор отменён.")
            return

        output_path = build_output_path()
        try:
            self.recorder.start(region, output_path)
        except Exception:
            restore_console()
            raise
        print(f"Запись началась: {output_path}")

    def _stop_recording(self) -> None:
        if self.recorder is None or not self.recorder.is_recording:
            return

        try:
            output_path = self.recorder.stop()
        finally:
            restore_console()
        if output_path is not None:
            print(f"Запись остановлена: {output_path}")

    def _report_ffmpeg_exit(self) -> None:
        if self.recorder is None:
            return

        error = self.recorder.poll_error()
        if error is None:
            return

        restore_console()
        print("FFmpeg остановился до завершения записи:")
        print(error)
        self.recorder.process = None
        time.sleep(0.2)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="record-screen",
        description="Запись выбранной области экрана с системным звуком и микрофоном.",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Запустить консольный режим с горячей клавишей вместо GUI.",
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
