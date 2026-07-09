from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TextIO

from .audio import AudioCapture, AudioCapturePaths
from .config import DEFAULT_FPS, RECORDINGS_DIR
from .selection import Region


@dataclass(frozen=True)
class RecordingOptions:
    show_cursor: bool = True
    system_audio: bool = True
    microphone: bool = True


def build_output_path(recordings_dir: Path = RECORDINGS_DIR) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return recordings_dir / f"screen_{stamp}.mp4"


def sibling_path(output_path: Path, suffix: str) -> Path:
    return output_path.with_name(f"{output_path.stem}.{suffix}")


def h264_safe_region(region: Region) -> Region:
    width = region.width - (region.width % 2)
    height = region.height - (region.height % 2)
    return Region(x=region.x, y=region.y, width=width, height=height)


def build_video_capture_command(
    ffmpeg_path: Path,
    region: Region,
    video_path: Path,
    fps: int = DEFAULT_FPS,
    show_cursor: bool = True,
) -> list[str]:
    safe_region = h264_safe_region(region)
    return [
        str(ffmpeg_path),
        "-y",
        "-f",
        "gdigrab",
        "-framerate",
        str(fps),
        "-draw_mouse",
        "1" if show_cursor else "0",
        "-offset_x",
        str(safe_region.x),
        "-offset_y",
        str(safe_region.y),
        "-video_size",
        f"{safe_region.width}x{safe_region.height}",
        "-i",
        "desktop",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
        str(video_path),
    ]


def build_mux_command(
    ffmpeg_path: Path,
    video_path: Path,
    system_audio_path: Path | None,
    microphone_audio_path: Path | None,
    output_path: Path,
) -> list[str]:
    audio_paths = [path for path in (system_audio_path, microphone_audio_path) if path is not None]
    command = [
        str(ffmpeg_path),
        "-y",
        "-i",
        str(video_path),
    ]
    for path in audio_paths:
        command.extend(["-i", str(path)])

    command.extend(["-map", "0:v"])
    if len(audio_paths) == 2:
        command.extend([
            "-filter_complex",
            "[1:a][2:a]amix=inputs=2:duration=longest:dropout_transition=0[a]",
            "-map",
            "[a]",
        ])
    elif len(audio_paths) == 1:
        command.extend(["-map", "1:a"])

    command.extend(["-c:v", "copy"])
    if audio_paths:
        command.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])
    command.extend(["-movflags", "+faststart", str(output_path)])
    return command


class ScreenRecorder:
    def __init__(
        self,
        ffmpeg_path: Path,
        fps: int = DEFAULT_FPS,
        audio_capture: AudioCapture | None = None,
    ) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.fps = fps
        self.audio_capture = audio_capture or AudioCapture()
        self.process: subprocess.Popen[str] | None = None
        self.output_path: Path | None = None
        self.video_path: Path | None = None
        self.audio_paths: AudioCapturePaths | None = None
        self.log_path: Path | None = None
        self._log_file: TextIO | None = None

    @property
    def is_recording(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def start(
        self,
        region: Region,
        output_path: Path,
        options: RecordingOptions | None = None,
    ) -> Path:
        if self.is_recording:
            raise RuntimeError("Запись уже идёт.")

        options = options or RecordingOptions()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path = output_path
        self.video_path = sibling_path(output_path, "video.mp4")
        self.log_path = sibling_path(output_path, "ffmpeg.log")
        self._log_file = self.log_path.open("w", encoding="utf-8", errors="replace")

        try:
            self.audio_paths = self.audio_capture.start(
                output_path,
                system_audio=options.system_audio,
                microphone=options.microphone,
            )
            command = build_video_capture_command(
                self.ffmpeg_path,
                region,
                self.video_path,
                fps=self.fps,
                show_cursor=options.show_cursor,
            )
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=self._log_file,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            self._close_log()
            self.audio_capture.stop()
            self.process = None
            raise

        return output_path

    def stop(self, timeout: float = 8.0) -> Path | None:
        if self.process is None:
            return None

        process = self.process
        output_path = self.output_path
        if process.poll() is None:
            try:
                if process.stdin is not None:
                    process.stdin.write("q\n")
                    process.stdin.flush()
            except OSError:
                pass
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=3)

        self._close_log()
        self.process = None
        audio_paths = self.audio_capture.stop()
        if output_path is not None and self.video_path is not None and audio_paths is not None:
            self._mux_recording(self.video_path, audio_paths, output_path)
            self._cleanup_temporary_files(self.video_path, audio_paths)
        return output_path

    def poll_error(self) -> str | None:
        if self.process is None or self.process.poll() is None:
            return None

        self._close_log()
        self.process = None
        try:
            self.audio_capture.stop()
        except Exception as exc:
            return str(exc)

        if self.log_path is None or not self.log_path.exists():
            return "FFmpeg завершился до остановки записи."
        log_text = self.log_path.read_text(encoding="utf-8", errors="replace").strip()
        return log_text or "FFmpeg завершился до остановки записи."

    def _mux_recording(self, video_path: Path, audio_paths: AudioCapturePaths, output_path: Path) -> None:
        command = build_mux_command(
            self.ffmpeg_path,
            video_path=video_path,
            system_audio_path=audio_paths.system,
            microphone_audio_path=audio_paths.microphone,
            output_path=output_path,
        )
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"Не удалось сохранить итоговую запись.\n\n{details}")

    def _cleanup_temporary_files(self, video_path: Path, audio_paths: AudioCapturePaths) -> None:
        for path in (video_path, audio_paths.system, audio_paths.microphone):
            if path is not None:
                path.unlink(missing_ok=True)

    def _close_log(self) -> None:
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None
