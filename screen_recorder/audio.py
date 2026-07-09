from __future__ import annotations

import threading
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


class AudioCaptureError(RuntimeError):
    pass


class MicrophoneAccessError(AudioCaptureError):
    pass


@dataclass(frozen=True)
class AudioCapturePaths:
    system: Path | None
    microphone: Path | None


def microphone_permission_help() -> str:
    return (
        "Не удалось открыть микрофон.\n"
        "Откройте Параметры Windows -> Конфиденциальность и безопасность -> Микрофон, "
        "затем разрешите доступ к микрофону для классических приложений."
    )


def choose_loopback_microphone(microphones: Iterable[object], default_speaker_name: str) -> object:
    loopbacks = [mic for mic in microphones if getattr(mic, "isloopback", False)]
    if not loopbacks:
        raise AudioCaptureError("Не найдено WASAPI loopback-устройство для записи системного звука.")

    for mic in loopbacks:
        if getattr(mic, "name", "") == default_speaker_name:
            return mic

    default_name = default_speaker_name.casefold()
    for mic in loopbacks:
        if default_name in getattr(mic, "name", "").casefold():
            return mic

    return loopbacks[0]


def float_block_to_pcm16(block: np.ndarray, channels: int = 2) -> bytes:
    samples = np.asarray(block, dtype=np.float32)
    if samples.ndim == 1:
        samples = samples.reshape(-1, 1)

    if samples.shape[1] < channels:
        samples = np.repeat(samples[:, :1], channels, axis=1)
    elif samples.shape[1] > channels:
        samples = samples[:, :channels]

    clipped = np.clip(samples, -1.0, 1.0)
    return (clipped * 32767).astype("<i2").tobytes()


def verify_microphone_access(sample_rate: int = 48_000) -> None:
    import soundcard as sc

    try:
        _probe_device(sc.default_microphone(), sample_rate=sample_rate)
    except Exception as exc:
        raise MicrophoneAccessError(f"{microphone_permission_help()}\n\n{exc}") from exc


def verify_system_audio_access(sample_rate: int = 48_000) -> None:
    import soundcard as sc

    speaker = sc.default_speaker()
    loopback = choose_loopback_microphone(sc.all_microphones(include_loopback=True), speaker.name)
    try:
        _probe_device(loopback, sample_rate=sample_rate)
    except Exception as exc:
        raise AudioCaptureError(f"Не удалось открыть системный звук через WASAPI loopback.\n\n{exc}") from exc


def _probe_device(device: object, sample_rate: int) -> None:
    with device.recorder(samplerate=sample_rate, channels=2) as recorder:
        recorder.record(numframes=max(1, sample_rate // 20))


class AudioCapture:
    def __init__(self, sample_rate: int = 48_000, channels: int = 2) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.paths: AudioCapturePaths | None = None
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._errors: list[BaseException] = []

    def start(
        self,
        output_path: Path,
        system_audio: bool = True,
        microphone: bool = True,
    ) -> AudioCapturePaths:
        import soundcard as sc

        if self._threads:
            raise AudioCaptureError("Запись аудио уже идёт.")

        self.paths = AudioCapturePaths(
            system=output_path.with_suffix(".system.wav") if system_audio else None,
            microphone=output_path.with_suffix(".microphone.wav") if microphone else None,
        )
        self._stop_event.clear()
        self._errors.clear()

        threads: list[threading.Thread] = []
        if system_audio and self.paths.system is not None:
            speaker = sc.default_speaker()
            system_device = choose_loopback_microphone(sc.all_microphones(include_loopback=True), speaker.name)
            threads.append(self._start_thread(system_device, self.paths.system, "system-audio"))
        if microphone and self.paths.microphone is not None:
            microphone_device = sc.default_microphone()
            threads.append(self._start_thread(microphone_device, self.paths.microphone, "microphone"))

        self._threads = threads
        return self.paths

    def stop(self) -> AudioCapturePaths | None:
        if not self._threads:
            return self.paths

        self._stop_event.set()
        for thread in self._threads:
            thread.join(timeout=3)
        self._threads.clear()

        if self._errors:
            raise AudioCaptureError(str(self._errors[0]))
        return self.paths

    def _start_thread(self, device: object, path: Path, name: str) -> threading.Thread:
        thread = threading.Thread(
            target=self._record_device,
            args=(device, path),
            name=name,
            daemon=True,
        )
        thread.start()
        return thread

    def _record_device(self, device: object, path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            block_frames = self.sample_rate // 10
            with device.recorder(samplerate=self.sample_rate, channels=self.channels) as recorder:
                with wave.open(str(path), "wb") as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(self.sample_rate)
                    while not self._stop_event.is_set():
                        block = recorder.record(numframes=block_frames)
                        wav_file.writeframes(float_block_to_pcm16(block, channels=self.channels))
        except BaseException as exc:
            self._errors.append(exc)
            self._stop_event.set()
