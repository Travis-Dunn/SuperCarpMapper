"""
Examine mode for editing tile examine text.

The examine text is displayed when a player examines a tile in-game.
"""

from __future__ import annotations

import tkinter as tk

from mapper.constants import DISPLAY_SIZE
from mapper.modes.base import EditorMode

# Maximum length for examine text
MAX_EXAMINE_LENGTH = 80


class ExamineMode(EditorMode):
    """Mode for editing tile examine text."""

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._selected_coords: tuple[int, int] | None = None
        self._original_text: str | None = None  # For discard functionality
        self._text_widget: tk.Text | None = None
        self._char_count_var: tk.StringVar | None = None

    def get_name(self) -> str:
        return "Examine"

    def get_status_hint(self) -> str:
        return "LMB: Select tile | Enter: Save | Esc: Discard | [P]aint [B]locked [E]xamine"

    def on_activate(self) -> None:
        self._selected_coords = None
        self._original_text = None
        self.editor.update_status("Select a tile to edit examine text")

    def on_deactivate(self) -> None:
        """Discard any pending edits when leaving this mode."""
        self._selected_coords = None
        self._original_text = None

    def on_map_click(self, world_x: int, world_y: int, event: tk.Event) -> None:
        """Select a tile and load its examine text."""
        coords = (world_x, world_y)
        tile = self.editor.tiles.get(coords)

        if tile is None:
            self.editor.update_status("No tile at this position")
            return

        # Select new tile (discards any unsaved edits on previous tile)
        self._selected_coords = coords
        self._original_text = tile.examine_text
        self._load_text_for_tile(tile)
        self._update_selection_overlay()

        # Focus the text widget for immediate editing
        if self._text_widget:
            self._text_widget.focus_set()

        self.editor.update_status(f"Editing ({world_x}, {world_y}) | Enter: Save | Esc: Discard")

    def _load_text_for_tile(self, tile) -> None:
        """Load the tile's examine text into the text widget."""
        if self._text_widget is None:
            return

        self._text_widget.delete("1.0", tk.END)
        if tile.examine_text:
            self._text_widget.insert("1.0", tile.examine_text)

        self._update_char_count()

    def _save_and_deselect(self, event: tk.Event = None) -> str:
        """Save the text and deselect the tile. Returns 'break' to stop event propagation."""
        if self._selected_coords is None or self._text_widget is None:
            return "break"

        tile = self.editor.tiles.get(self._selected_coords)
        if tile is None:
            return "break"

        # Get text, strip trailing whitespace/newlines, enforce max length
        text = self._text_widget.get("1.0", tk.END).rstrip()
        text = text[:MAX_EXAMINE_LENGTH]

        # Store None for empty string
        tile.examine_text = text if text else None

        saved_coords = self._selected_coords
        self._deselect()
        self.editor.update_status(f"Saved examine text for ({saved_coords[0]}, {saved_coords[1]})")

        return "break"

    def _discard_and_deselect(self, event: tk.Event = None) -> str:
        """Discard changes and deselect the tile. Returns 'break' to stop event propagation."""
        if self._selected_coords is None:
            return "break"

        discarded_coords = self._selected_coords
        self._deselect()
        self.editor.update_status(
            f"Discarded changes for ({discarded_coords[0]}, {discarded_coords[1]})"
        )

        return "break"

    def _deselect(self) -> None:
        """Clear selection state and UI."""
        self._selected_coords = None
        self._original_text = None

        if self._text_widget:
            self._text_widget.delete("1.0", tk.END)

        self._update_char_count()
        self._update_selection_overlay()

    def _update_char_count(self) -> None:
        """Update the character count display."""
        if self._text_widget is None or self._char_count_var is None:
            return

        text = self._text_widget.get("1.0", tk.END).rstrip()
        count = len(text)
        self._char_count_var.set(f"{count}/{MAX_EXAMINE_LENGTH}")

    def _on_text_changed(self, event: tk.Event = None) -> None:
        """Handle text changes - enforce max length and update counter."""
        if self._text_widget is None:
            return

        text = self._text_widget.get("1.0", tk.END).rstrip()

        # Enforce max length by truncating
        if len(text) > MAX_EXAMINE_LENGTH:
            cursor_pos = self._text_widget.index(tk.INSERT)

            self._text_widget.delete("1.0", tk.END)
            self._text_widget.insert("1.0", text[:MAX_EXAMINE_LENGTH])

            try:
                self._text_widget.mark_set(tk.INSERT, cursor_pos)
            except tk.TclError:
                self._text_widget.mark_set(tk.INSERT, tk.END)

        self._update_char_count()

    def _update_selection_overlay(self) -> None:
        """Draw selection rectangle around selected tile."""
        editor = self.editor

        # Clear old selection overlay
        editor.map_canvas.delete("selection")

        if self._selected_coords is None:
            return

        tile_x, tile_y = self._selected_coords
        px = editor.world_to_canvas_x(tile_x)
        py = editor.world_to_canvas_y(tile_y)

        editor.map_canvas.create_rectangle(
            px, py,
            px + DISPLAY_SIZE, py + DISPLAY_SIZE,
            outline="#00ffff",
            width=3,
            tags=("overlay", "selection")
        )

    def render_overlay(self) -> None:
        """Render the selection overlay."""
        self._update_selection_overlay()

    def build_panel(self, parent: tk.Frame) -> tk.Frame:
        """Build the examine text editing panel."""
        frame = tk.Frame(parent)

        tk.Label(frame, text="Examine Text").pack(pady=(10, 5))

        # Instructions
        tk.Label(
            frame,
            text="Click a tile to select,\nthen edit text below.",
            justify=tk.LEFT,
            fg="#666"
        ).pack(padx=10, pady=(0, 10))

        # Character count
        self._char_count_var = tk.StringVar(value=f"0/{MAX_EXAMINE_LENGTH}")
        tk.Label(frame, textvariable=self._char_count_var).pack()

        # Text widget with scrollbar
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            width=20,
            height=6,
            yscrollcommand=scrollbar.set
        )
        self._text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._text_widget.yview)

        # Bind events
        self._text_widget.bind("<KeyRelease>", self._on_text_changed)
        self._text_widget.bind("<Return>", self._save_and_deselect)
        self._text_widget.bind("<Escape>", self._discard_and_deselect)

        # Keybinding hints
        tk.Label(
            frame,
            text="Enter: Save\nEscape: Discard",
            justify=tk.LEFT,
            fg="#666",
            font=("TkDefaultFont", 9)
        ).pack(pady=(5, 10))

        return frame