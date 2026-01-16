"""
Base class for editor modes.

To create a new mode:
1. Subclass EditorMode
2. Override the methods you need
3. Register it in editor.py's setup_modes()
"""

from __future__ import annotations

import tkinter as tk
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mapper.editor import Mapper


class EditorMode(ABC):
    """
    Base class for editor modes.

    Each mode handles a specific editing task (painting tiles, setting blocked
    state, editing examine text, etc.). Modes are responsible for:
    - Handling map clicks/drags
    - Rendering overlays on the map
    - Building their UI panel
    """

    def __init__(self, editor: Mapper) -> None:
        self.editor = editor

    @abstractmethod
    def get_name(self) -> str:
        """Return mode name for status bar display."""
        pass

    def get_status_hint(self) -> str:
        """Return help text shown in status bar."""
        return ""

    def on_activate(self) -> None:
        """Called when switching to this mode."""
        pass

    def on_deactivate(self) -> None:
        """Called when leaving this mode."""
        pass

    def on_map_click(self, world_x: int, world_y: int, event: tk.Event) -> None:
        """Handle left click on map."""
        pass

    def on_map_drag(self, world_x: int, world_y: int, event: tk.Event) -> None:
        """Handle drag on map."""
        pass

    def on_map_right_click(self, world_x: int, world_y: int, event: tk.Event) -> None:
        """Handle right click on map."""
        pass

    def render_overlay(self) -> None:
        """Draw mode-specific visuals on map canvas."""
        pass

    def build_panel(self, parent: tk.Frame) -> tk.Frame | None:
        """
        Build and return a widget for the left panel.

        Args:
            parent: Parent frame to contain the panel.

        Returns:
            A Frame widget, or None if this mode has no panel.
        """
        return None
