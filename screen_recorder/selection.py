from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import MIN_REGION_SIZE


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int


def normalize_region(start_x: int, start_y: int, end_x: int, end_y: int) -> Region:
    x = min(start_x, end_x)
    y = min(start_y, end_y)
    return Region(x=x, y=y, width=abs(end_x - start_x), height=abs(end_y - start_y))


def is_valid_region(region: Region, min_size: int = MIN_REGION_SIZE) -> bool:
    return region.width >= min_size and region.height >= min_size


def _geometry(width: int, height: int, x: int, y: int) -> str:
    return f"{width}x{height}{x:+d}{y:+d}"


def select_region() -> Optional[Region]:
    import tkinter as tk

    result: Optional[Region] = None
    start_x = 0
    start_y = 0
    rect_id: Optional[int] = None

    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.35)

    virtual_x = root.winfo_vrootx()
    virtual_y = root.winfo_vrooty()
    virtual_width = root.winfo_vrootwidth()
    virtual_height = root.winfo_vrootheight()

    root.geometry(_geometry(virtual_width, virtual_height, virtual_x, virtual_y))
    root.configure(cursor="crosshair", background="black")

    canvas = tk.Canvas(root, background="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    def on_press(event: tk.Event) -> None:
        nonlocal start_x, start_y, rect_id
        start_x = event.x_root
        start_y = event.y_root
        if rect_id is not None:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="#00aaff",
            width=3,
            fill="#3aa0ff",
            stipple="gray25",
        )

    def on_drag(event: tk.Event) -> None:
        if rect_id is None:
            return
        canvas.coords(
            rect_id,
            start_x - virtual_x,
            start_y - virtual_y,
            event.x_root - virtual_x,
            event.y_root - virtual_y,
        )

    def on_release(event: tk.Event) -> None:
        nonlocal result
        region = normalize_region(start_x, start_y, event.x_root, event.y_root)
        if is_valid_region(region):
            result = region
        root.quit()

    def cancel(_event: tk.Event | None = None) -> None:
        root.quit()

    root.bind("<Escape>", cancel)
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.deiconify()
    root.lift()
    root.focus_force()
    root.mainloop()
    root.destroy()
    return result

