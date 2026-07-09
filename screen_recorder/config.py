import sys
from pathlib import Path


def detect_project_root(
    frozen: bool | None = None,
    executable: str | Path | None = None,
) -> Path:
    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))
    if executable is None:
        executable = sys.executable

    if frozen:
        return Path(executable).resolve().parent
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = detect_project_root()
RECORDINGS_DIR = PROJECT_ROOT / "recordings"
TOOLS_DIR = PROJECT_ROOT / "tools"
FFMPEG_DIR = TOOLS_DIR / "ffmpeg"

HOTKEY = "ctrl+alt+shift+r"
DEFAULT_FPS = 20
MIN_REGION_SIZE = 20

FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
