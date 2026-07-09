from types import SimpleNamespace

import numpy as np

from screen_recorder.audio import choose_loopback_microphone, float_block_to_pcm16, microphone_permission_help


def test_microphone_permission_help_mentions_windows_settings():
    help_text = microphone_permission_help()

    assert "Windows Settings" in help_text
    assert "Microphone" in help_text
    assert "desktop apps" in help_text


def test_choose_loopback_microphone_prefers_default_speaker_name():
    headphones = SimpleNamespace(name="USB Headphones", isloopback=True)
    speaker = SimpleNamespace(name="Onboard Speaker", isloopback=True)
    microphone = SimpleNamespace(name="Onboard Microphone", isloopback=False)

    assert choose_loopback_microphone([microphone, headphones, speaker], "Onboard Speaker") is speaker


def test_float_block_to_pcm16_clips_and_outputs_stereo_bytes():
    block = np.array([[-2.0], [0.0], [2.0]], dtype=np.float32)

    pcm = float_block_to_pcm16(block, channels=2)
    values = np.frombuffer(pcm, dtype="<i2").reshape(-1, 2)

    assert values.tolist() == [[-32767, -32767], [0, 0], [32767, 32767]]
