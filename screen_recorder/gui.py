from __future__ import annotations

import os
import queue
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from .audio import AudioCaptureError, MicrophoneAccessError, verify_microphone_access, verify_system_audio_access
from .config import RECORDINGS_DIR
from .ffmpeg_manager import ensure_ffmpeg
from .recorder import RecordingOptions, ScreenRecorder, build_output_path
from .selection import Region, select_region
from .settings import (
    AppSettings,
    TRAY_BEHAVIOR_CLOSE,
    TRAY_BEHAVIOR_CLOSE_AND_MINIMIZE,
    TRAY_BEHAVIOR_MINIMIZE,
    TRAY_BEHAVIOR_NONE,
    load_settings,
    save_settings,
)
from .tray import TrayController

WINDOW_GEOMETRY = "980x620"
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 580
LEFT_PANEL_MIN_WIDTH = 560
RECORDINGS_PANEL_MIN_WIDTH = 240
RECORDINGS_LIST_VISIBLE_ROWS = 5
DETAILS_TEXT_VISIBLE_ROWS = 3

TRAY_BEHAVIOR_LABELS = {
    TRAY_BEHAVIOR_NONE: "Не скрывать в трей",
    TRAY_BEHAVIOR_CLOSE: "Скрывать по крестику",
    TRAY_BEHAVIOR_MINIMIZE: "Скрывать при сворачивании",
    TRAY_BEHAVIOR_CLOSE_AND_MINIMIZE: "Скрывать по крестику и при сворачивании",
}
TRAY_BEHAVIOR_BY_LABEL = {label: behavior for behavior, label in TRAY_BEHAVIOR_LABELS.items()}


class RecorderStatus(Enum):
    READY = "Готово"
    SELECTING = "Выбор области"
    RECORDING = "Идёт запись"
    FINALIZING = "Сохранение"
    ERROR = "Ошибка"


@dataclass
class GuiState:
    status: RecorderStatus = RecorderStatus.READY
    region: Region | None = None
    system_audio: bool = True
    microphone: bool = True
    show_cursor: bool = True
    output_path: Path | None = None
    recording_started_at: float | None = None
    error_details: str = ""


def format_region_summary(region: Region | None) -> str:
    if region is None:
        return "Область не выбрана"
    return f"{region.width} x {region.height}, координаты {region.x},{region.y}"


def recent_recordings(recordings_dir: Path = RECORDINGS_DIR, limit: int = 5) -> list[Path]:
    if not recordings_dir.exists():
        return []
    files = [path for path in recordings_dir.glob("*.mp4") if path.is_file()]
    return sorted(files, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)[:limit]


class RecorderGui:
    def __init__(
        self,
        recorder_factory: Callable[[Path], ScreenRecorder] | None = None,
        region_selector: Callable[[], Region | None] = select_region,
    ) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = tk.Tk()
        self.root.title("Запись экрана")
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.configure(bg="#111827")

        self.settings = load_settings()
        self.state = GuiState()
        self.recorder_factory = recorder_factory or (lambda ffmpeg_path: ScreenRecorder(ffmpeg_path))
        self.region_selector = region_selector
        self.recorder: ScreenRecorder | None = None
        self.hotkey_registered = False
        self.hotkey_handle: object | None = None
        self.current_hotkey = self.settings.hotkey
        self.hidden_to_tray = False
        self.tray_actions: queue.Queue[str] = queue.Queue()
        self.tray = TrayController(
            on_show=lambda: self.tray_actions.put("show"),
            on_exit=lambda: self.tray_actions.put("exit"),
        )

        self.status_var = tk.StringVar(value=self.state.status.value)
        self.area_var = tk.StringVar(value=format_region_summary(None))
        self.timer_var = tk.StringVar(value="00:00")
        self.system_audio_var = tk.BooleanVar(value=True)
        self.microphone_var = tk.BooleanVar(value=True)
        self.show_cursor_var = tk.BooleanVar(value=True)
        self.audio_status_var = tk.StringVar(value="Аудио не проверено")
        self.last_file_var = tk.StringVar(value="Записей пока нет")
        self.hotkey_var = tk.StringVar(value=self.settings.hotkey)
        self.hotkey_header_var = tk.StringVar(value=f"Горячая клавиша: {self.settings.hotkey}")
        self.tray_behavior_var = tk.StringVar(value=TRAY_BEHAVIOR_LABELS[self.settings.tray_behavior])

        self._configure_style()
        self._build_layout()
        self._refresh_recordings()
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)
        self.root.bind("<Unmap>", self._handle_unmap, add="+")

    def run(self) -> int:
        self._set_status(RecorderStatus.READY, "Подготовка локального FFmpeg...")
        try:
            ffmpeg_path = ensure_ffmpeg()
            self.recorder = self.recorder_factory(ffmpeg_path)
            self._register_hotkey()
            self._set_status(RecorderStatus.READY, "Готово")
        except Exception as exc:
            self._show_error(exc)

        self._tick()
        self.root.mainloop()
        return 0

    def request_close(self) -> None:
        if self.settings.tray_behavior in {TRAY_BEHAVIOR_CLOSE, TRAY_BEHAVIOR_CLOSE_AND_MINIMIZE}:
            self.hide_to_tray()
            return
        self.exit_app()

    def close(self) -> None:
        self.exit_app()

    def exit_app(self) -> None:
        try:
            self.tray.stop()
            self._unregister_hotkey()
            if self.recorder is not None and self.recorder.is_recording:
                self.recorder.stop()
        finally:
            self.root.destroy()

    def hide_to_tray(self) -> None:
        try:
            self.tray.show()
        except Exception as exc:
            self._show_error(RuntimeError(f"Не удалось скрыть окно в трей.\n\n{exc}"))
            return

        self.hidden_to_tray = True
        self.root.withdraw()

    def show_from_tray(self) -> None:
        self.hidden_to_tray = False
        self.tray.hide()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _handle_unmap(self, event: object) -> None:
        if getattr(event, "widget", None) is not self.root or self.hidden_to_tray:
            return
        if self.root.state() != "iconic":
            return
        if self.settings.tray_behavior in {TRAY_BEHAVIOR_MINIMIZE, TRAY_BEHAVIOR_CLOSE_AND_MINIMIZE}:
            self.root.after(0, self.hide_to_tray)

    def toggle_recording(self) -> None:
        if self.recorder is not None and self.recorder.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        if self.recorder is None:
            self._show_error(RuntimeError("Запись ещё не готова."))
            return

        try:
            self._check_audio()
            if self.state.region is None:
                self._select_region_for_recording()
            if self.state.region is None:
                self._set_status(RecorderStatus.READY, "Выбор отменён")
                return

            output_path = build_output_path()
            options = RecordingOptions(
                show_cursor=self.show_cursor_var.get(),
                system_audio=self.system_audio_var.get(),
                microphone=self.microphone_var.get(),
            )
            self.root.iconify()
            self.recorder.start(self.state.region, output_path, options=options)
            self.state.output_path = output_path
            self.state.recording_started_at = time.monotonic()
            self._set_status(RecorderStatus.RECORDING, f"Запись в файл {output_path.name}")
            self.start_button.configure(text="Стоп", style="Danger.TButton")
        except Exception as exc:
            self.root.deiconify()
            self._show_error(exc)

    def stop_recording(self) -> None:
        if self.recorder is None or not self.recorder.is_recording:
            return

        self._set_status(RecorderStatus.FINALIZING, "Сохраняю MP4...")
        self.root.update_idletasks()
        try:
            output_path = self.recorder.stop()
            self.root.deiconify()
            self.state.recording_started_at = None
            self.start_button.configure(text="Старт", style="Accent.TButton")
            self._set_status(RecorderStatus.READY, f"Сохранено: {output_path.name if output_path else 'запись'}")
            self._refresh_recordings()
        except Exception as exc:
            self.root.deiconify()
            self._show_error(exc)

    def select_area(self) -> None:
        self._select_region_for_recording()
        self._set_status(RecorderStatus.READY, "Готово")

    def open_recordings_folder(self) -> None:
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(RECORDINGS_DIR)

    def open_selected_recording(self) -> None:
        path = self._selected_recording()
        if path is not None:
            os.startfile(path)

    def show_selected_recording(self) -> None:
        path = self._selected_recording()
        if path is not None:
            subprocess.Popen(["explorer", "/select,", str(path)])

    def _select_region_for_recording(self) -> None:
        self._set_status(RecorderStatus.SELECTING, "Выберите область. Esc отменяет выбор.")
        self.root.withdraw()
        try:
            region = self.region_selector()
        finally:
            self.root.deiconify()
        if region is not None:
            self.state.region = region
            self.area_var.set(format_region_summary(region))

    def _check_audio(self) -> None:
        checks: list[str] = []
        if self.microphone_var.get():
            verify_microphone_access()
            checks.append("микрофон")
        if self.system_audio_var.get():
            verify_system_audio_access()
            checks.append("системный звук")
        self.audio_status_var.set("Аудио готово: " + ", ".join(checks) if checks else "Аудио выключено")

    def _set_status(self, status: RecorderStatus, message: str | None = None) -> None:
        self.state.status = status
        self.status_var.set(status.value)
        if message is not None:
            self.details_text.configure(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.insert("1.0", message)
            self.details_text.configure(state="disabled")

    def _show_error(self, error: BaseException) -> None:
        self.state.error_details = str(error)
        self.state.recording_started_at = None
        self.start_button.configure(text="Старт", style="Accent.TButton")
        self._set_status(RecorderStatus.ERROR, str(error))

    def _tick(self) -> None:
        self._handle_tray_actions()
        if self.state.recording_started_at is not None:
            elapsed = max(0, int(time.monotonic() - self.state.recording_started_at))
            minutes, seconds = divmod(elapsed, 60)
            self.timer_var.set(f"{minutes:02d}:{seconds:02d}")
        else:
            self.timer_var.set("00:00")

        if self.recorder is not None:
            error = self.recorder.poll_error()
            if error is not None:
                self.root.deiconify()
                self._show_error(RuntimeError(error))
                self._refresh_recordings()
        self.root.after(500, self._tick)

    def _handle_tray_actions(self) -> None:
        while True:
            try:
                action = self.tray_actions.get_nowait()
            except queue.Empty:
                return

            if action == "show":
                self.show_from_tray()
            elif action == "exit":
                self.exit_app()

    def save_current_settings(self) -> None:
        hotkey = self.hotkey_var.get().strip().lower()
        if not hotkey:
            self._show_error(RuntimeError("Горячая клавиша не может быть пустой."))
            return

        tray_behavior = TRAY_BEHAVIOR_BY_LABEL.get(self.tray_behavior_var.get(), TRAY_BEHAVIOR_NONE)
        previous_settings = self.settings
        previous_hotkey = self.current_hotkey

        try:
            if hotkey != self.current_hotkey:
                self._unregister_hotkey()
                self._register_hotkey(hotkey)
            self.settings = AppSettings(hotkey=hotkey, tray_behavior=tray_behavior)
            save_settings(self.settings)
            self.hotkey_header_var.set(f"Горячая клавиша: {hotkey}")
            self._set_status(RecorderStatus.READY, "Настройки сохранены")
        except Exception as exc:
            self.settings = previous_settings
            self.hotkey_var.set(previous_hotkey)
            self.tray_behavior_var.set(TRAY_BEHAVIOR_LABELS[previous_settings.tray_behavior])
            self._unregister_hotkey()
            try:
                self._register_hotkey(previous_hotkey)
            except Exception:
                pass
            self._show_error(RuntimeError(f"Не удалось применить горячую клавишу.\n\n{exc}"))

    def _register_hotkey(self, hotkey: str | None = None) -> None:
        if self.hotkey_registered:
            return
        import keyboard

        self.current_hotkey = hotkey or self.current_hotkey
        self.hotkey_handle = keyboard.add_hotkey(self.current_hotkey, lambda: self.root.after(0, self.toggle_recording))
        self.hotkey_registered = True

    def _unregister_hotkey(self) -> None:
        if not self.hotkey_registered:
            return
        import keyboard

        if self.hotkey_handle is not None:
            keyboard.remove_hotkey(self.hotkey_handle)
        else:
            keyboard.unhook_all_hotkeys()
        self.hotkey_handle = None
        self.hotkey_registered = False

    def _refresh_recordings(self) -> None:
        self.recordings_list.delete(0, "end")
        self.recording_paths = recent_recordings()
        for path in self.recording_paths:
            self.recordings_list.insert("end", path.name)
        self.last_file_var.set(self.recording_paths[0].name if self.recording_paths else "Записей пока нет")

    def _selected_recording(self) -> Path | None:
        selection = self.recordings_list.curselection()
        if not selection:
            return self.recording_paths[0] if self.recording_paths else None
        index = int(selection[0])
        return self.recording_paths[index] if index < len(self.recording_paths) else None

    def _configure_style(self) -> None:
        style = self.ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10))
        style.configure("App.TFrame", background="#111827")
        style.configure("Panel.TFrame", background="#1f2937", relief="flat")
        style.configure("Title.TLabel", background="#111827", foreground="#f9fafb", font=("Segoe UI", 18, "bold"))
        style.configure("Muted.TLabel", background="#111827", foreground="#9ca3af")
        style.configure("Panel.TLabel", background="#1f2937", foreground="#e5e7eb")
        style.configure("Status.TLabel", background="#1f2937", foreground="#93c5fd", font=("Segoe UI", 12, "bold"))
        style.configure("Timer.TLabel", background="#1f2937", foreground="#f9fafb", font=("Consolas", 26, "bold"))
        style.configure("Accent.TButton", background="#ef4444", foreground="#ffffff", padding=(16, 8), font=("Segoe UI", 12, "bold"))
        style.map("Accent.TButton", background=[("active", "#dc2626")])
        style.configure("Danger.TButton", background="#991b1b", foreground="#ffffff", padding=(16, 8), font=("Segoe UI", 12, "bold"))
        style.map("Danger.TButton", background=[("active", "#7f1d1d")])
        style.configure("Secondary.TButton", background="#374151", foreground="#e5e7eb", padding=(10, 7))
        style.map("Secondary.TButton", background=[("active", "#4b5563")])
        style.configure("Toggle.TCheckbutton", background="#1f2937", foreground="#e5e7eb")
        style.map("Toggle.TCheckbutton", background=[("active", "#1f2937")])

    def _build_layout(self) -> None:
        ttk = self.ttk
        tk = self.tk

        outer = ttk.Frame(self.root, style="App.TFrame", padding=16)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Запись экрана", style="Title.TLabel").pack(side="left")
        ttk.Label(header, textvariable=self.hotkey_header_var, style="Muted.TLabel").pack(side="right")

        main = ttk.Frame(outer, style="App.TFrame")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3, minsize=LEFT_PANEL_MIN_WIDTH)
        main.columnconfigure(1, weight=1, minsize=RECORDINGS_PANEL_MIN_WIDTH)
        main.rowconfigure(0, weight=1)

        left = ttk.Frame(main, style="Panel.TFrame", padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        ttk.Label(left, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")
        ttk.Label(left, textvariable=self.timer_var, style="Timer.TLabel").pack(anchor="w", pady=(4, 10))

        self.start_button = ttk.Button(left, text="Старт", style="Accent.TButton", command=self.toggle_recording)
        self.start_button.pack(fill="x", pady=(0, 8))

        area_row = ttk.Frame(left, style="Panel.TFrame")
        area_row.pack(fill="x", pady=(4, 8))
        ttk.Label(area_row, text="Область захвата", style="Panel.TLabel").pack(anchor="w")
        ttk.Label(area_row, textvariable=self.area_var, style="Panel.TLabel").pack(anchor="w", pady=(2, 6))
        ttk.Button(area_row, text="Выбрать область", style="Secondary.TButton", command=self.select_area).pack(fill="x")

        toggles = ttk.Frame(left, style="Panel.TFrame")
        toggles.pack(fill="x", pady=(6, 8))
        for column in range(3):
            toggles.columnconfigure(column, weight=1)
        ttk.Checkbutton(toggles, text="Звук системы", variable=self.system_audio_var, style="Toggle.TCheckbutton").grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Checkbutton(toggles, text="Микрофон", variable=self.microphone_var, style="Toggle.TCheckbutton").grid(row=0, column=1, sticky="w", padx=(0, 12))
        ttk.Checkbutton(toggles, text="Показывать курсор", variable=self.show_cursor_var, style="Toggle.TCheckbutton").grid(row=0, column=2, sticky="w")
        ttk.Label(left, textvariable=self.audio_status_var, style="Panel.TLabel").pack(anchor="w", pady=(2, 0))

        settings = ttk.Frame(left, style="Panel.TFrame")
        settings.pack(fill="x", pady=(10, 8))
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="Горячая клавиша", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        ttk.Entry(settings, textvariable=self.hotkey_var).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(0, 6))
        ttk.Button(settings, text="Сохранить", style="Secondary.TButton", command=self.save_current_settings).grid(row=0, column=2, sticky="ew", pady=(0, 6))
        ttk.Label(settings, text="Трей", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10))
        self.tray_behavior_combo = ttk.Combobox(
            settings,
            textvariable=self.tray_behavior_var,
            values=list(TRAY_BEHAVIOR_LABELS.values()),
            state="readonly",
        )
        self.tray_behavior_combo.grid(row=1, column=1, columnspan=2, sticky="ew")

        self.details_text = tk.Text(
            left,
            height=DETAILS_TEXT_VISIBLE_ROWS,
            wrap="word",
            bg="#111827",
            fg="#d1d5db",
            insertbackground="#f9fafb",
            relief="flat",
            padx=10,
            pady=8,
        )
        self.details_text.pack(fill="both", expand=True, pady=(8, 0))
        self.details_text.configure(state="disabled")

        right = ttk.Frame(main, style="Panel.TFrame", padding=14)
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Label(right, text="Последние записи", style="Status.TLabel").pack(anchor="w")
        ttk.Label(right, textvariable=self.last_file_var, style="Panel.TLabel").pack(anchor="w", pady=(4, 8))

        self.recordings_list = tk.Listbox(
            right,
            height=RECORDINGS_LIST_VISIBLE_ROWS,
            width=32,
            bg="#111827",
            fg="#e5e7eb",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            activestyle="none",
            relief="flat",
            highlightthickness=0,
        )
        self.recordings_list.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Button(right, text="Открыть", style="Secondary.TButton", command=self.open_selected_recording).pack(fill="x", pady=(0, 6))
        ttk.Button(right, text="Показать в папке", style="Secondary.TButton", command=self.show_selected_recording).pack(fill="x", pady=(0, 6))
        ttk.Button(right, text="Папка записей", style="Secondary.TButton", command=self.open_recordings_folder).pack(fill="x")
