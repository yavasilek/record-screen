from __future__ import annotations

import subprocess
from pathlib import Path


def test_launcher_help_hides_pip_satisfied_output():
    project_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        ["cmd", "/c", "RecordScreen.bat", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    output = completed.stdout + completed.stderr

    assert completed.returncode == 0
    assert "usage: record-screen" in output
    assert "Запись выбранной области" in output
    assert "Requirement already satisfied" not in output


def test_launcher_uses_pythonw_for_normal_gui_startup():
    project_root = Path(__file__).resolve().parents[1]
    launcher = (project_root / "RecordScreen.ps1").read_text(encoding="utf-8")

    assert "pythonw.exe" in launcher
    assert "$AppArgs.Count -eq 0" in launcher
