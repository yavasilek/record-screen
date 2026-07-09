from pathlib import Path

from screen_recorder.recorder import build_mux_command, build_video_capture_command
from screen_recorder.selection import Region


def test_build_video_capture_command_records_desktop_region_without_audio():
    command = build_video_capture_command(
        ffmpeg_path=Path("tools/ffmpeg/bin/ffmpeg.exe"),
        region=Region(x=10, y=20, width=640, height=360),
        video_path=Path("recordings/out.video.mp4"),
        fps=20,
    )

    assert command[:2] == ["tools\\ffmpeg\\bin\\ffmpeg.exe", "-y"]
    assert "gdigrab" in command
    assert "-offset_x" in command
    assert command[command.index("-offset_x") + 1] == "10"
    assert command[command.index("-offset_y") + 1] == "20"
    assert command[command.index("-video_size") + 1] == "640x360"
    assert "wasapi" not in command
    assert command[-1] == "recordings\\out.video.mp4"


def test_build_video_capture_command_trims_odd_dimensions_for_h264():
    command = build_video_capture_command(
        ffmpeg_path=Path("tools/ffmpeg/bin/ffmpeg.exe"),
        region=Region(x=11, y=8, width=1891, height=1213),
        video_path=Path("recordings/out.video.mp4"),
        fps=20,
    )

    assert command[command.index("-video_size") + 1] == "1890x1212"


def test_build_video_capture_command_can_hide_cursor():
    command = build_video_capture_command(
        ffmpeg_path=Path("tools/ffmpeg/bin/ffmpeg.exe"),
        region=Region(x=0, y=0, width=640, height=360),
        video_path=Path("recordings/out.video.mp4"),
        fps=20,
        show_cursor=False,
    )

    assert command[command.index("-draw_mouse") + 1] == "0"


def test_build_mux_command_mixes_system_and_microphone_audio():
    command = build_mux_command(
        ffmpeg_path=Path("tools/ffmpeg/bin/ffmpeg.exe"),
        video_path=Path("recordings/out.video.mp4"),
        system_audio_path=Path("recordings/out.system.wav"),
        microphone_audio_path=Path("recordings/out.microphone.wav"),
        output_path=Path("recordings/out.mp4"),
    )

    assert command[:2] == ["tools\\ffmpeg\\bin\\ffmpeg.exe", "-y"]
    assert command.count("-i") == 3
    assert "recordings\\out.video.mp4" in command
    assert "recordings\\out.system.wav" in command
    assert "recordings\\out.microphone.wav" in command
    assert any("amix=inputs=2:duration=longest:dropout_transition=0" in part for part in command)
    assert command[-1] == "recordings\\out.mp4"


def test_build_mux_command_supports_system_audio_only():
    command = build_mux_command(
        ffmpeg_path=Path("tools/ffmpeg/bin/ffmpeg.exe"),
        video_path=Path("recordings/out.video.mp4"),
        system_audio_path=Path("recordings/out.system.wav"),
        microphone_audio_path=None,
        output_path=Path("recordings/out.mp4"),
    )

    assert command.count("-i") == 2
    assert "recordings\\out.system.wav" in command
    assert "-filter_complex" not in command
    assert command[-1] == "recordings\\out.mp4"


def test_build_mux_command_supports_video_only_output():
    command = build_mux_command(
        ffmpeg_path=Path("tools/ffmpeg/bin/ffmpeg.exe"),
        video_path=Path("recordings/out.video.mp4"),
        system_audio_path=None,
        microphone_audio_path=None,
        output_path=Path("recordings/out.mp4"),
    )

    assert command.count("-i") == 1
    assert "-filter_complex" not in command
    assert "-c:a" not in command
    assert command[-1] == "recordings\\out.mp4"
