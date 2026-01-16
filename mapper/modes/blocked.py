"""
Blocked mode for marking tiles as impassable.
"""

from __future__ import annotations

import tkinter as tk

from mapper.constants import DISPLAY_SIZE
from mapper.modes.base import EditorMode


class BlockedMode(EditorMode):
    """Mode for marking tiles as blocked (impassable)."""

    def get_name(self) -> str:
        return "Blocked"

    def get_status_hint(self) -> str:
        return "LMB: Toggle blocked | Ctrl+LMB: Pan | Hotkeys: [P]aint [B]locked"

    def on_activate(self) -> None:
        blocked_count = sum(1 for t in self.editor.tiles.values() if t.blocked)
        self.editor.update_status(f"{blocked_count} blocked tiles")

    def on_map_click(self, world_x: int, world_y: int, event: tk.Event) -> None:
        self._toggle_blocked(world_x, world_y)

    def _toggle_blocked(self, tile_x: int, tile_y: int) -> None:
        """Toggle the blocked state of the tile at the given coordinates."""
        editor = self.editor
        coords = (tile_x, tile_y)

        # Check if there's a tile at this position
        tile = editor.tiles.get(coords)
        if tile is None:
            editor.update_status("No tile at this position")
            return

        # Toggle blocked state
        tile.blocked = not tile.blocked
        state = "blocked" if tile.blocked else "passable"

        # Update just this tile's overlay
        self._update_tile_overlay(tile_x, tile_y)

        blocked_count = sum(1 for t in editor.tiles.values() if t.blocked)
        editor.update_status(
            f"Tile ({tile_x}, {tile_y}) now {state} | {blocked_count} blocked total"
        )

    def _update_tile_overlay(self, tile_x: int, tile_y: int) -> None:
        """Update the overlay for a single tile."""
        editor = self.editor
        tag = f"blocked_{tile_x}_{tile_y}"

        # Remove existing overlay for this tile
        editor.map_canvas.delete(tag)

        # Draw new overlay if blocked
        tile = editor.tiles.get((tile_x, tile_y))
        if tile and tile.blocked:
            self._draw_blocked_indicator(tile_x, tile_y, tag)

    def _draw_blocked_indicator(self, tile_x: int, tile_y: int, tag: str) -> None:
        """Draw a red circle indicator for a blocked tile."""
        editor = self.editor

        px = editor.world_to_canvas_x(tile_x)
        py = editor.world_to_canvas_y(tile_y)

        center_x = px + DISPLAY_SIZE // 2
        center_y = py + DISPLAY_SIZE // 2
        radius = DISPLAY_SIZE // 4

        editor.map_canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill="#cc0000",
            outline="#ff0000",
            width=2,
            tags=("overlay", tag)
        )

    def render_overlay(self) -> None:
        """Draw blocked indicators on all blocked tiles."""
        for (tile_x, tile_y), tile in self.editor.tiles.items():
            if tile.blocked:
                tag = f"blocked_{tile_x}_{tile_y}"
                self._draw_blocked_indicator(tile_x, tile_y, tag)

    def build_panel(self, parent: tk.Frame) -> tk.Frame:
        """Build a simple info panel."""
        frame = tk.Frame(parent)

        tk.Label(frame, text="Blocked Mode").pack(pady=10)
        tk.Label(
            frame,
            text="Click tiles to toggle\nblocked state.\n\nBlocked tiles show\na red circle.",
            justify=tk.LEFT
        ).pack(padx=10, pady=5)

        return frame
