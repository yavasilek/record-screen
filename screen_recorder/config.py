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


def detect_bundle_root(
    frozen: bool | None = None,
    meipass: str | Path | None = None,
) -> Path | None:
    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))
    if meipass is None:
        meipass = getattr(sys, "_MEIPASS", None)

    if frozen and meipass:
        return Path(meipass).resolve()
    return None


PROJECT_ROOT = detect_project_root()
BUNDLE_ROOT = detect_bundle_root()
RECORDINGS_DIR = PROJECT_ROOT / "recordings"
TOOLS_DIR = PROJECT_ROOT / "tools"
FFMPEG_DIR = TOOLS_DIR / "ffmpeg"

HOTKEY = "ctrl+alt+shift+r"
DEFAULT_FPS = 20
MIN_REGION_SIZE = 20

FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
