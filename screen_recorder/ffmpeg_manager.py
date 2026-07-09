from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

from .config import BUNDLE_ROOT, FFMPEG_DIR, FFMPEG_DOWNLOAD_URL, PROJECT_ROOT


def find_local_ffmpeg(
    project_root: Path = PROJECT_ROOT,
    bundle_root: Path | None = BUNDLE_ROOT,
) -> Path | None:
    for root in (project_root, bundle_root):
        if root is None:
            continue
        ffmpeg = _find_ffmpeg_under(root)
        if ffmpeg is not None:
            return ffmpeg
    return None


def _find_ffmpeg_under(root: Path) -> Path | None:
    standard_path = root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    if standard_path.exists():
        return standard_path

    ffmpeg_dir = root / "tools" / "ffmpeg"
    if not ffmpeg_dir.exists():
        return None

    matches = sorted(ffmpeg_dir.rglob("ffmpeg.exe"))
    return matches[0] if matches else None


def ensure_ffmpeg(
    project_root: Path = PROJECT_ROOT,
    bundle_root: Path | None = BUNDLE_ROOT,
) -> Path:
    existing = find_local_ffmpeg(project_root, bundle_root)
    if existing is not None:
        return existing

    target_dir = project_root / "tools" / "ffmpeg"
    target_dir.mkdir(parents=True, exist_ok=True)
    archive_path = target_dir / "ffmpeg.zip"

    print("FFmpeg не найден локально. Скачиваю portable-сборку...")
    _download_file(FFMPEG_DOWNLOAD_URL, archive_path)
    _extract_archive(archive_path, target_dir)
    archive_path.unlink(missing_ok=True)

    downloaded = find_local_ffmpeg(project_root)
    if downloaded is None:
        raise RuntimeError(f"Не удалось найти ffmpeg.exe после распаковки в {target_dir}")
    return downloaded


def _download_file(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url) as response, destination.open("wb") as file:
        shutil.copyfileobj(response, file)


def _extract_archive(archive_path: Path, target_dir: Path = FFMPEG_DIR) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(target_dir)
