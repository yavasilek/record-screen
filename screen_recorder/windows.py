from __future__ import annotations

import ctypes
import sys

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
PROCESS_PER_MONITOR_DPI_AWARE = 2
SW_MINIMIZE = 6
SW_RESTORE = 9


def enable_dpi_awareness() -> bool:
    if sys.platform != "win32":
        return False

    try:
        result = ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        )
        if result:
            return True
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
        return True
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return True
    except (AttributeError, OSError):
        return False


def minimize_console() -> bool:
    return _show_console(SW_MINIMIZE)


def restore_console() -> bool:
    return _show_console(SW_RESTORE)


def _show_console(command: int) -> bool:
    if sys.platform != "win32":
        return False

    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if not hwnd:
        return False
    return bool(ctypes.windll.user32.ShowWindow(hwnd, command))
