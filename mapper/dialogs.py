"""
Custom dialog classes for the Mapper application.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from mapper.constants import PALETTE

if TYPE_CHECKING:
    pass


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Convert hex color string to RGB tuple, or None if invalid."""
    if not hex_color.startswith("#"):
        return None
    hex_part = hex_color[1:]
    if len(hex_part) == 3:
        hex_part = "".join(c * 2 for c in hex_part)
    if len(hex_part) != 6:
        return None
    try:
        r = int(hex_part[0:2], 16)
        g = int(hex_part[2:4], 16)
        b = int(hex_part[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None


class ColorPickerDialog(tk.Toplevel):
    """
    A simple dialog for picking a color from the fixed palette.

    Usage:
        dialog = ColorPickerDialog(parent, current_color="#000000")
        if dialog.result is not None:
            new_color = dialog.result  # hex string like "#ff0000"
    """

    SWATCH_SIZE = 48
    SWATCHES_PER_ROW = 4

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        current_color: str = "#000000",
        title: str = "Select Color"
    ) -> None:
        super().__init__(parent)

        self.result: str | None = None
        self._current_color = current_color

        self.title(title)
        self.transient(parent)
        self.resizable(False, False)

        self._build_ui()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Modal behavior
        self.grab_set()
        self.wait_window()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Current color display
        current_frame = tk.Frame(self)
        current_frame.pack(pady=(10, 5), padx=10)

        tk.Label(current_frame, text="Current:").pack(side=tk.LEFT)
        self._current_swatch = tk.Canvas(
            current_frame,
            width=self.SWATCH_SIZE,
            height=24,
            bg=self._current_color,
            highlightthickness=1,
            highlightbackground="#666"
        )
        self._current_swatch.pack(side=tk.LEFT, padx=(5, 0))

        # Palette grid
        palette_frame = tk.Frame(self)
        palette_frame.pack(pady=10, padx=10)

        for idx, rgb in enumerate(PALETTE):
            row = idx // self.SWATCHES_PER_ROW
            col = idx % self.SWATCHES_PER_ROW

            hex_color = rgb_to_hex(rgb)

            swatch = tk.Canvas(
                palette_frame,
                width=self.SWATCH_SIZE,
                height=self.SWATCH_SIZE,
                bg=hex_color,
                highlightthickness=2,
                highlightbackground="#444"
            )
            swatch.grid(row=row, column=col, padx=2, pady=2)

            # Bind click - need to capture hex_color in closure
            swatch.bind("<Button-1>", lambda e, c=hex_color: self._select_color(c))

            # Highlight if this is the current color
            if hex_color.lower() == self._current_color.lower():
                swatch.configure(highlightbackground="#ffff00", highlightthickness=3)

        # Cancel button
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=(5, 10))

        tk.Button(btn_frame, text="Cancel", command=self._cancel).pack()

    def _select_color(self, hex_color: str) -> None:
        """Handle color selection."""
        self.result = hex_color
        self.destroy()

    def _cancel(self) -> None:
        """Handle cancel."""
        self.result = None
        self.destroy()