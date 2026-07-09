from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class TrayController:
    def __init__(
        self,
        on_show: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self.on_show = on_show
        self.on_exit = on_exit
        self.icon: Any | None = None
        self.thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self.icon is not None

    def show(self) -> None:
        if self.icon is not None:
            return

        import pystray

        self.icon = pystray.Icon(
            "RecordScreen",
            _create_icon_image(),
            "Запись экрана",
            menu=pystray.Menu(
                pystray.MenuItem("Показать", self._show_window),
                pystray.MenuItem("Выход", self._exit_app),
            ),
        )
        self.thread = threading.Thread(target=self.icon.run, name="record-screen-tray", daemon=True)
        self.thread.start()

    def hide(self) -> None:
        if self.icon is None:
            return
        icon = self.icon
        self.icon = None
        try:
            icon.stop()
        finally:
            self.thread = None

    def stop(self) -> None:
        self.hide()

    def _show_window(self, icon: object | None = None, item: object | None = None) -> None:
        self.on_show()

    def _exit_app(self, icon: object | None = None, item: object | None = None) -> None:
        self.on_exit()


def _create_icon_image() -> object:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (17, 24, 39, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 10, 56, 46), radius=8, fill=(31, 41, 55), outline=(229, 231, 235), width=3)
    draw.ellipse((24, 24, 40, 40), fill=(239, 68, 68))
    draw.rectangle((20, 50, 44, 55), fill=(229, 231, 235))
    return image
