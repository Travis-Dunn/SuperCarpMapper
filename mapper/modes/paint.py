"""
Paint mode for placing tile sprites on the map.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from mapper.constants import DISPLAY_SIZE, WORLD_OFFSET
from mapper.modes.base import EditorMode
from mapper.tile import Tile

if TYPE_CHECKING:
    from mapper.editor import Mapper


class PaintTileMode(EditorMode):
    """Mode for painting tile sprites onto the map."""

    def __init__(self, editor: Mapper) -> None:
        super().__init__(editor)
        self.palette_canvas: tk.Canvas | None = None

    def get_name(self) -> str:
        return "Paint"

    def get_status_hint(self) -> str:
        return "LMB: Paint | Ctrl+LMB: Pan | Hotkeys: [P]aint [B]locked"

    def on_activate(self) -> None:
        self.editor.update_status(f"Brush: tile {self.editor.brush}")

    def on_map_click(self, world_x: int, world_y: int, event: tk.Event) -> None:
        self._paint_tile(world_x, world_y)

    def on_map_drag(self, world_x: int, world_y: int, event: tk.Event) -> None:
        self._paint_tile(world_x, world_y)

    def _paint_tile(self, tile_x: int, tile_y: int) -> None:
        """Paint the current brush at the given world coordinates."""
        editor = self.editor

        if not editor.tile_images:
            return

        # Bounds check
        if not (-WORLD_OFFSET <= tile_x < WORLD_OFFSET):
            return
        if not (-WORLD_OFFSET <= tile_y < WORLD_OFFSET):
            return

        coords = (tile_x, tile_y)

        # Check if already painted with same tile
        existing = editor.tiles.get(coords)
        if existing and existing.sprite == editor.brush:
            return

        # Remove old tile image if present
        editor.map_canvas.delete(f"maptile_{tile_x}_{tile_y}")

        # Paint new tile
        px = editor.world_to_canvas_x(tile_x)
        py = editor.world_to_canvas_y(tile_y)
        editor.map_canvas.create_image(
            px, py,
            anchor=tk.NW,
            image=editor.tile_images[editor.brush],
            tags=("maptile", f"maptile_{tile_x}_{tile_y}")
        )

        # Update or create tile
        if existing:
            existing.sprite = editor.brush
        else:
            editor.tiles[coords] = Tile(sprite=editor.brush)

    def build_panel(self, parent: tk.Frame) -> tk.Frame:
        """Build the tile palette panel."""
        frame = tk.Frame(parent)

        tk.Label(frame, text="Tile Palette").pack()

        palette_container = tk.Frame(frame)
        palette_container.pack(fill=tk.BOTH, expand=True)

        self.palette_canvas = tk.Canvas(palette_container, bg="#333")
        palette_scrollbar = tk.Scrollbar(
            palette_container,
            orient=tk.VERTICAL,
            command=self.palette_canvas.yview
        )
        self.palette_canvas.configure(yscrollcommand=palette_scrollbar.set)

        palette_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.palette_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.palette_canvas.bind("<Button-1>", self._on_palette_click)

        # Draw the palette after the widget is mapped
        frame.after(50, self._refresh_palette)

        return frame

    def _refresh_palette(self) -> None:
        """Redraw the palette canvas with all tiles."""
        if self.palette_canvas is None:
            return

        self.palette_canvas.delete("all")

        editor = self.editor
        if not editor.tile_images:
            return

        # Figure out how many tiles fit per row
        self.palette_canvas.update_idletasks()
        canvas_width = self.palette_canvas.winfo_width()
        if canvas_width < DISPLAY_SIZE:
            canvas_width = 200  # Fallback

        tiles_per_row = max(1, canvas_width // DISPLAY_SIZE)
        tile_count = len(editor.tile_images)
        rows = (tile_count + tiles_per_row - 1) // tiles_per_row

        for idx in range(tile_count):
            px = (idx % tiles_per_row) * DISPLAY_SIZE
            py = (idx // tiles_per_row) * DISPLAY_SIZE

            self.palette_canvas.create_image(
                px, py,
                anchor=tk.NW,
                image=editor.tile_images[idx],
                tags=f"tile_{idx}"
            )

        # Highlight current brush
        self._highlight_brush(tiles_per_row)

        # Update scroll region
        self.palette_canvas.configure(
            scrollregion=(0, 0, tiles_per_row * DISPLAY_SIZE, rows * DISPLAY_SIZE)
        )

    def _highlight_brush(self, tiles_per_row: int) -> None:
        """Draw selection rectangle around current brush tile."""
        if self.palette_canvas is None:
            return

        self.palette_canvas.delete("highlight")

        editor = self.editor
        px = (editor.brush % tiles_per_row) * DISPLAY_SIZE
        py = (editor.brush // tiles_per_row) * DISPLAY_SIZE

        self.palette_canvas.create_rectangle(
            px, py,
            px + DISPLAY_SIZE, py + DISPLAY_SIZE,
            outline="#ffff00",
            width=2,
            tags="highlight"
        )

    def _on_palette_click(self, event: tk.Event) -> None:
        """Select a tile from the palette as the current brush."""
        editor = self.editor

        if not editor.tile_images:
            return

        canvas_width = self.palette_canvas.winfo_width()
        tiles_per_row = max(1, canvas_width // DISPLAY_SIZE)

        # Convert canvas coords to tile index
        cx = self.palette_canvas.canvasx(event.x)
        cy = self.palette_canvas.canvasy(event.y)

        tile_x = int(cx) // DISPLAY_SIZE
        tile_y = int(cy) // DISPLAY_SIZE
        idx = tile_y * tiles_per_row + tile_x

        if idx in editor.tile_images:
            editor.brush = idx
            self._highlight_brush(tiles_per_row)
            editor.update_status(f"Brush: tile {idx}")
