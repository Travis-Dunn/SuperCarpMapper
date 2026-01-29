"""
Character mode for placing and editing NPC positions.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from mapper.character import Character
from mapper.constants import DISPLAY_SIZE
from mapper.modes.base import EditorMode


class CharacterMode(EditorMode):
    """Mode for placing and editing NPC positions."""

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._selected_coords: tuple[int, int] | None = None

        # Panel widgets
        self._coords_var: tk.StringVar | None = None
        self._name_var: tk.StringVar | None = None
        self._name_entry: tk.Entry | None = None
        self._save_btn: tk.Button | None = None
        self._delete_btn: tk.Button | None = None

    def get_name(self) -> str:
        return "Character"

    def get_status_hint(self) -> str:
        return "LMB: Select tile | Esc: Unfocus fields | [P]aint [B]locked [E]xamine [S]pawn [C]haracter"

    def on_activate(self) -> None:
        self._selected_coords = None
        char_count = len(self.editor.characters)
        self.editor.update_status(f"{char_count} character(s) on map")

    def on_deactivate(self) -> None:
        self._selected_coords = None

    def on_map_click(self, world_x: int, world_y: int, event: tk.Event) -> None:
        """Select a tile for character editing."""
        # Unfocus any Entry widgets so hotkeys work after clicking map
        self.editor.map_canvas.focus_set()

        coords = (world_x, world_y)

        # Check if there's a tile here (characters should be on tiles)
        if coords not in self.editor.tiles:
            self.editor.update_status("No tile at this position - place a tile first")
            return

        self._selected_coords = coords
        self._load_character_data()
        self._update_selection_overlay()
        self._update_button_states()

        character = self.editor.characters.get(coords)
        if character:
            self.editor.update_status(f"Editing character at ({world_x}, {world_y}): {character.name}")
        else:
            self.editor.update_status(f"Selected ({world_x}, {world_y}) - fill in name to add character")

    def _load_character_data(self) -> None:
        """Load character data into the panel fields."""
        if self._selected_coords is None:
            self._clear_fields()
            return

        self._coords_var.set(f"({self._selected_coords[0]}, {self._selected_coords[1]})")

        character = self.editor.characters.get(self._selected_coords)
        if character:
            self._name_var.set(character.name)
        else:
            self._name_var.set("")

    def _clear_fields(self) -> None:
        """Clear all panel fields."""
        if self._coords_var:
            self._coords_var.set("(none)")
        if self._name_var:
            self._name_var.set("")

    def _update_button_states(self) -> None:
        """Enable/disable buttons based on selection state."""
        has_selection = self._selected_coords is not None
        has_character = has_selection and self._selected_coords in self.editor.characters

        if self._save_btn:
            self._save_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        if self._delete_btn:
            self._delete_btn.config(state=tk.NORMAL if has_character else tk.DISABLED)

    def _unfocus(self, event: tk.Event = None) -> str:
        """Remove focus from Entry widgets so hotkeys work again."""
        self.editor.map_canvas.focus_set()
        return "break"

    def _save_character(self) -> None:
        """Save the current field values as a character."""
        if self._selected_coords is None:
            return

        name = self._name_var.get().strip()

        # Validate name
        if not name:
            messagebox.showwarning("Validation Error", "Name is required")
            return

        # Save character
        self.editor.characters[self._selected_coords] = Character(name=name)

        self._update_button_states()
        self._refresh_overlay()

        char_count = len(self.editor.characters)
        self.editor.update_status(
            f"Saved character '{name}' at {self._selected_coords} | {char_count} total"
        )

    def _delete_character(self) -> None:
        """Delete the character at the selected coordinates."""
        if self._selected_coords is None:
            return

        if self._selected_coords not in self.editor.characters:
            return

        name = self.editor.characters[self._selected_coords].name
        del self.editor.characters[self._selected_coords]

        self._load_character_data()  # Refresh fields
        self._update_button_states()
        self._refresh_overlay()

        char_count = len(self.editor.characters)
        self.editor.update_status(
            f"Deleted character '{name}' | {char_count} remaining"
        )

    def _refresh_overlay(self) -> None:
        """Refresh the character overlay."""
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
            outline="#00ffff",  # Cyan for character mode
            width=3,
            tags=("overlay", "selection")
        )

    def render_overlay(self) -> None:
        """Draw character indicators on all character positions."""
        self._update_selection_overlay()

        for (tile_x, tile_y), character in self.editor.characters.items():
            self._draw_character_indicator(tile_x, tile_y, character)

    def _draw_character_indicator(
        self,
        tile_x: int,
        tile_y: int,
        character: Character
    ) -> None:
        """Draw a character indicator."""
        editor = self.editor

        px = editor.world_to_canvas_x(tile_x)
        py = editor.world_to_canvas_y(tile_y)

        # Draw a circle
        cx = px + DISPLAY_SIZE // 2
        cy = py + DISPLAY_SIZE // 2
        radius = DISPLAY_SIZE // 3

        editor.map_canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            fill="#009999",
            outline="#00ffff",
            width=2,
            tags=("overlay", f"char_{tile_x}_{tile_y}")
        )

        # Draw name label below the circle
        editor.map_canvas.create_text(
            cx, cy, # Approximately centered
            text=character.name,
            fill="#000000",
            font=("TkDefaultFont", 8),
            tags=("overlay", f"char_{tile_x}_{tile_y}")
        )

    def build_panel(self, parent: tk.Frame) -> tk.Frame:
        """Build the character editing panel."""
        frame = tk.Frame(parent)

        tk.Label(frame, text="Characters", font=("TkDefaultFont", 10, "bold")).pack(pady=(10, 5))

        # Instructions
        tk.Label(
            frame,
            text="Click a tile to select,\nthen edit character properties.",
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

        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)

        self._save_btn = tk.Button(
            btn_frame,
            text="Save Character",
            command=self._save_character,
            state=tk.DISABLED
        )
        self._save_btn.pack(side=tk.LEFT, padx=(0, 5))

        self._delete_btn = tk.Button(
            btn_frame,
            text="Delete",
            command=self._delete_character,
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
            text="Characters show as cyan\ncircles on the map.",
            justify=tk.LEFT,
            fg="#666",
            font=("TkDefaultFont", 9)
        ).pack(padx=10, pady=(0, 10))

        return frame