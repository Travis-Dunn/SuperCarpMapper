"""
Spawn mode for placing and editing monster spawn points.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from mapper.constants import DISPLAY_SIZE
from mapper.modes.base import EditorMode
from mapper.monsterspawn import MonsterSpawn


class SpawnMode(EditorMode):
    """Mode for placing and editing monster spawn points."""

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._selected_coords: tuple[int, int] | None = None

        # Panel widgets
        self._coords_var: tk.StringVar | None = None
        self._name_var: tk.StringVar | None = None
        self._respawn_var: tk.StringVar | None = None
        self._name_entry: tk.Entry | None = None
        self._respawn_entry: tk.Entry | None = None
        self._save_btn: tk.Button | None = None
        self._delete_btn: tk.Button | None = None

    def get_name(self) -> str:
        return "Spawn"

    def get_status_hint(self) -> str:
        return "LMB: Select tile | Esc: Unfocus fields | [P]aint [B]locked [E]xamine [S]pawn"

    def on_activate(self) -> None:
        self._selected_coords = None
        spawn_count = len(self.editor.spawns)
        self.editor.update_status(f"{spawn_count} spawn(s) on map")

    def on_deactivate(self) -> None:
        self._selected_coords = None

    def on_map_click(self, world_x: int, world_y: int, event: tk.Event) -> None:
        """Select a tile for spawn editing."""
        # Unfocus any Entry widgets so hotkeys work after clicking map
        self.editor.map_canvas.focus_set()

        coords = (world_x, world_y)

        # Check if there's a tile here (spawns should be on tiles)
        if coords not in self.editor.tiles:
            self.editor.update_status("No tile at this position - place a tile first")
            return

        self._selected_coords = coords
        self._load_spawn_data()
        self._update_selection_overlay()
        self._update_button_states()

        spawn = self.editor.spawns.get(coords)
        if spawn:
            self.editor.update_status(f"Editing spawn at ({world_x}, {world_y}): {spawn.name}")
        else:
            self.editor.update_status(f"Selected ({world_x}, {world_y}) - fill in fields to add spawn")

    def _load_spawn_data(self) -> None:
        """Load spawn data into the panel fields."""
        if self._selected_coords is None:
            self._clear_fields()
            return

        self._coords_var.set(f"({self._selected_coords[0]}, {self._selected_coords[1]})")

        spawn = self.editor.spawns.get(self._selected_coords)
        if spawn:
            self._name_var.set(spawn.name)
            self._respawn_var.set(str(spawn.respawn_ticks))
        else:
            self._name_var.set("")
            self._respawn_var.set("100")  # Default

    def _clear_fields(self) -> None:
        """Clear all panel fields."""
        if self._coords_var:
            self._coords_var.set("(none)")
        if self._name_var:
            self._name_var.set("")
        if self._respawn_var:
            self._respawn_var.set("")

    def _update_button_states(self) -> None:
        """Enable/disable buttons based on selection state."""
        has_selection = self._selected_coords is not None
        has_spawn = has_selection and self._selected_coords in self.editor.spawns

        if self._save_btn:
            self._save_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        if self._delete_btn:
            self._delete_btn.config(state=tk.NORMAL if has_spawn else tk.DISABLED)

    def _unfocus(self, event: tk.Event = None) -> str:
        """Remove focus from Entry widgets so hotkeys work again."""
        self.editor.map_canvas.focus_set()
        return "break"

    def _save_spawn(self) -> None:
        """Save the current field values as a spawn."""
        if self._selected_coords is None:
            return

        name = self._name_var.get().strip()
        respawn_str = self._respawn_var.get().strip()

        # Validate name
        if not name:
            messagebox.showwarning("Validation Error", "Name is required")
            return

        # Validate respawn ticks
        try:
            respawn_ticks = int(respawn_str)
            if respawn_ticks < 1:
                raise ValueError("Must be positive")
        except ValueError:
            messagebox.showwarning("Validation Error", "Respawn ticks must be a positive integer")
            return

        # Save spawn
        self.editor.spawns[self._selected_coords] = MonsterSpawn(
            name=name,
            respawn_ticks=respawn_ticks
        )

        self._update_button_states()
        self._refresh_overlay()

        spawn_count = len(self.editor.spawns)
        self.editor.update_status(
            f"Saved spawn '{name}' at {self._selected_coords} | {spawn_count} total"
        )

    def _delete_spawn(self) -> None:
        """Delete the spawn at the selected coordinates."""
        if self._selected_coords is None:
            return

        if self._selected_coords not in self.editor.spawns:
            return

        name = self.editor.spawns[self._selected_coords].name
        del self.editor.spawns[self._selected_coords]

        self._load_spawn_data()  # Refresh fields (will show defaults)
        self._update_button_states()
        self._refresh_overlay()

        spawn_count = len(self.editor.spawns)
        self.editor.update_status(
            f"Deleted spawn '{name}' | {spawn_count} remaining"
        )

    def _refresh_overlay(self) -> None:
        """Refresh the spawn overlay."""
        self.editor.map_canvas.delete("overlay")
        self.render_overlay()

    def _update_selection_overlay(self) -> None:
        """Draw selection rectangle around selected tile."""
        editor = self.editor

        # Clear old selection
        editor.map_canvas.delete("selection")

        if self._selected_coords is None:
            return

        tile_x, tile_y = self._selected_coords
        px = editor.world_to_canvas_x(tile_x)
        py = editor.world_to_canvas_y(tile_y)

        editor.map_canvas.create_rectangle(
            px, py,
            px + DISPLAY_SIZE, py + DISPLAY_SIZE,
            outline="#ff00ff",  # Magenta for spawn mode
            width=3,
            tags=("overlay", "selection")
        )

    def render_overlay(self) -> None:
        """Draw spawn indicators on all spawn points."""
        self._update_selection_overlay()

        for (tile_x, tile_y), spawn in self.editor.spawns.items():
            self._draw_spawn_indicator(tile_x, tile_y, spawn)

    def _draw_spawn_indicator(
        self,
        tile_x: int,
        tile_y: int,
        spawn: MonsterSpawn
    ) -> None:
        """Draw a spawn point indicator."""
        editor = self.editor

        px = editor.world_to_canvas_x(tile_x)
        py = editor.world_to_canvas_y(tile_y)

        # Draw a diamond shape
        cx = px + DISPLAY_SIZE // 2
        cy = py + DISPLAY_SIZE // 2
        size = DISPLAY_SIZE // 3

        editor.map_canvas.create_polygon(
            cx, cy - size,      # Top
            cx + size, cy,      # Right
            cx, cy + size,      # Bottom
            cx - size, cy,      # Left
            fill="#9900ff",
            outline="#cc66ff",
            width=2,
            tags=("overlay", f"spawn_{tile_x}_{tile_y}")
        )

        # Draw name label below the diamond
        editor.map_canvas.create_text(
            cx, cy + size + 8,
            text=spawn.name,
            fill="#cc66ff",
            font=("TkDefaultFont", 8),
            tags=("overlay", f"spawn_{tile_x}_{tile_y}")
        )

    def build_panel(self, parent: tk.Frame) -> tk.Frame:
        """Build the spawn editing panel."""
        frame = tk.Frame(parent)

        tk.Label(frame, text="Monster Spawns", font=("TkDefaultFont", 10, "bold")).pack(pady=(10, 5))

        # Instructions
        tk.Label(
            frame,
            text="Click a tile to select,\nthen edit spawn properties.",
            justify=tk.LEFT,
            fg="#666"
        ).pack(padx=10, pady=(0, 10))

        # Selected coordinates display
        self._coords_var = tk.StringVar(value="(none)")
        coords_frame = tk.Frame(frame)
        coords_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(coords_frame, text="Tile:").pack(side=tk.LEFT)
        tk.Label(coords_frame, textvariable=self._coords_var, fg="#0066cc").pack(side=tk.LEFT, padx=5)

        # Separator
        tk.Frame(frame, height=1, bg="#ccc").pack(fill=tk.X, padx=10, pady=10)

        # Name field
        name_frame = tk.Frame(frame)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(name_frame, text="Name:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self._name_var = tk.StringVar()
        self._name_entry = tk.Entry(name_frame, textvariable=self._name_var)
        self._name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._name_entry.bind("<Escape>", self._unfocus)

        # Respawn ticks field
        respawn_frame = tk.Frame(frame)
        respawn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(respawn_frame, text="Respawn ticks:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self._respawn_var = tk.StringVar(value="100")
        self._respawn_entry = tk.Entry(respawn_frame, textvariable=self._respawn_var, width=10)
        self._respawn_entry.pack(side=tk.LEFT)
        self._respawn_entry.bind("<Escape>", self._unfocus)

        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)

        self._save_btn = tk.Button(
            btn_frame,
            text="Save Spawn",
            command=self._save_spawn,
            state=tk.DISABLED
        )
        self._save_btn.pack(side=tk.LEFT, padx=(0, 5))

        self._delete_btn = tk.Button(
            btn_frame,
            text="Delete",
            command=self._delete_spawn,
            state=tk.DISABLED
        )
        self._delete_btn.pack(side=tk.LEFT)

        # Separator
        tk.Frame(frame, height=1, bg="#ccc").pack(fill=tk.X, padx=10, pady=10)

        # Keybinding hints
        tk.Label(
            frame,
            text="Esc: Unfocus fields\n(then hotkeys work)",
            justify=tk.LEFT,
            fg="#666",
            font=("TkDefaultFont", 9)
        ).pack(pady=(5, 5))

        # Visual hint
        tk.Label(
            frame,
            text="Spawns show as purple\ndiamonds on the map.",
            justify=tk.LEFT,
            fg="#666",
            font=("TkDefaultFont", 9)
        ).pack(padx=10, pady=(0, 10))

        return frame