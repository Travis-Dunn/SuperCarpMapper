"""
Main Mapper editor class.

This module contains the core editor window and UI setup.
Mode-specific logic is delegated to classes in the modes/ package.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from PIL import Image, ImageTk

from mapper.constants import (
    DISPLAY_SIZE,
    GRID_RANGE,
    SPRITE_SIZE,
    WORLD_OFFSET,
    WORLD_SIZE,
)
from mapper.map_io import load_map, save_map
from mapper.modes import BlockedMode, EditorMode, ExamineMode, PaintTileMode, SpawnMode
from mapper.monsterspawn import MonsterSpawn
from mapper.tile import Tile

if TYPE_CHECKING:
    pass


class Mapper:
    """
    Main tile map editor application.

    Manages the editor window, mode system, and shared state.
    Individual editing behaviors are handled by EditorMode subclasses.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Mapper")

        # Atlas state
        self.atlas_path: str | None = None
        self.atlas_image: Image.Image | None = None
        self.tile_images: dict[int, ImageTk.PhotoImage] = {}
        self.tile_pil_images: dict[int, Image.Image] = {}

        # Editing state
        self.brush: int = 0
        self.tiles: dict[tuple[int, int], Tile] = {}
        self.spawns: dict[tuple[int, int], MonsterSpawn] = {}

        # Navigation state
        self._is_panning: bool = False

        # Mode system
        self._modes: dict[str, EditorMode] = {}
        self._mode_keys: dict[str, str] = {}  # hotkey -> mode_name
        self._current_mode: EditorMode | None = None
        self._current_mode_name: str | None = None

        # UI references
        self._left_panel_container: tk.Frame | None = None
        self._current_panel: tk.Frame | None = None
        self.map_canvas: tk.Canvas | None = None
        self._status_var: tk.StringVar | None = None

        self._setup_ui()
        self._setup_modes()

    # =========================================================================
    # Mode System
    # =========================================================================

    def _setup_modes(self) -> None:
        """Register all editor modes."""
        self._register_mode("paint", PaintTileMode(self), "p")
        self._register_mode("blocked", BlockedMode(self), "b")
        self._register_mode("examine", ExamineMode(self), "e")
        self._register_mode("spawn", SpawnMode(self), "s")
        self.set_mode("paint")

    def _register_mode(
        self,
        name: str,
        mode: EditorMode,
        hotkey: str | None = None
    ) -> None:
        """Register an editor mode with optional hotkey."""
        self._modes[name] = mode
        if hotkey:
            self._mode_keys[hotkey.lower()] = name

    def set_mode(self, name: str) -> None:
        """Switch to a different editor mode."""
        if name not in self._modes:
            return

        if self._current_mode:
            self._current_mode.on_deactivate()

        self._current_mode_name = name
        self._current_mode = self._modes[name]
        self._current_mode.on_activate()

        self._rebuild_panel()
        self._refresh_overlay()
        self.update_status()

    def _rebuild_panel(self) -> None:
        """Rebuild the left panel for the current mode."""
        if self._current_panel:
            self._current_panel.destroy()
            self._current_panel = None

        if self._current_mode:
            self._current_panel = self._current_mode.build_panel(self._left_panel_container)
            if self._current_panel:
                self._current_panel.pack(fill=tk.BOTH, expand=True)

    def _refresh_overlay(self) -> None:
        """Refresh mode-specific overlay on map canvas."""
        self.map_canvas.delete("overlay")

        if self._current_mode:
            self._current_mode.render_overlay()

    def update_status(self, message: str | None = None) -> None:
        """Update status bar with mode info and optional message."""
        if not self._current_mode:
            return

        mode_name = self._current_mode.get_name()
        if message:
            self._status_var.set(f"[{mode_name}] {message}")
        else:
            hint = self._current_mode.get_status_hint()
            self._status_var.set(f"[{mode_name}] {hint}")

    # =========================================================================
    # UI Setup
    # =========================================================================

    def _setup_ui(self) -> None:
        """Initialize the user interface."""
        self._setup_menu()
        self._setup_main_layout()
        self._setup_status_bar()
        self._setup_bindings()

        # Draw grid and center view
        self._draw_map_grid()
        self.root.after(100, lambda: self.center_view_on(0, 0))

    def _setup_menu(self) -> None:
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Atlas...", command=self._load_atlas)
        file_menu.add_separator()
        file_menu.add_command(label="Load Map...", command=self._load_map)
        file_menu.add_command(label="Save Map...", command=self._save_map)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def _setup_main_layout(self) -> None:
        """Setup the main paned window layout."""
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel: mode-specific UI
        self._left_panel_container = tk.Frame(paned)
        paned.add(self._left_panel_container, width=200)

        # Right panel: map canvas
        right_frame = tk.Frame(paned)
        paned.add(right_frame)

        tk.Label(right_frame, text="Map").pack()

        map_container = tk.Frame(right_frame)
        map_container.pack(fill=tk.BOTH, expand=True)

        self.map_canvas = tk.Canvas(
            map_container,
            bg="#1a1a1a",
            scrollregion=(0, 0, WORLD_SIZE * DISPLAY_SIZE, WORLD_SIZE * DISPLAY_SIZE)
        )

        scrollbar_v = tk.Scrollbar(
            map_container,
            orient=tk.VERTICAL,
            command=self.map_canvas.yview
        )
        scrollbar_h = tk.Scrollbar(
            map_container,
            orient=tk.HORIZONTAL,
            command=self.map_canvas.xview
        )
        self.map_canvas.configure(
            yscrollcommand=scrollbar_v.set,
            xscrollcommand=scrollbar_h.set
        )

        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.map_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _setup_status_bar(self) -> None:
        """Setup the status bar at the bottom."""
        self._status_var = tk.StringVar(value="Load an atlas to begin")
        status_bar = tk.Label(
            self.root,
            textvariable=self._status_var,
            anchor=tk.W,
            relief=tk.SUNKEN
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        self.map_canvas.bind("<Button-1>", self._on_map_click)
        self.map_canvas.bind("<B1-Motion>", self._on_map_drag)
        self.map_canvas.bind("<ButtonRelease-1>", self._on_map_release)
        self.map_canvas.bind("<Button-3>", self._on_map_right_click)
        self.root.bind("<Key>", self._on_key)

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_key(self, event: tk.Event) -> None:
        """Handle hotkey presses."""

        # Ignore hotkeys when typing in a text widget
        if isinstance(self.root.focus_get(), (tk.Text, tk.Entry)):
            return

        key = event.char.lower()
        if key in self._mode_keys:
            self.set_mode(self._mode_keys[key])

    def _on_map_click(self, event: tk.Event) -> None:
        """Handle map click (delegate to mode or pan)."""
        # Check for Ctrl key (pan mode)
        if event.state & 0x0004:
            self._is_panning = True
            self.map_canvas.scan_mark(event.x, event.y)
            self.map_canvas.config(cursor="fleur")
            return

        if not self._current_mode:
            return

        world_x, world_y = self._event_to_world(event)
        self._current_mode.on_map_click(world_x, world_y, event)

    def _on_map_drag(self, event: tk.Event) -> None:
        """Handle map drag (delegate to mode or pan)."""
        if self._is_panning:
            self.map_canvas.scan_dragto(event.x, event.y, gain=1)
            return

        if not self._current_mode:
            return

        world_x, world_y = self._event_to_world(event)
        self._current_mode.on_map_drag(world_x, world_y, event)

    def _on_map_release(self, event: tk.Event) -> None:
        """Handle mouse release."""
        if self._is_panning:
            self._is_panning = False
            self.map_canvas.config(cursor="")

    def _on_map_right_click(self, event: tk.Event) -> None:
        """Delegate map right-click to current mode."""
        if not self._current_mode:
            return

        world_x, world_y = self._event_to_world(event)
        self._current_mode.on_map_right_click(world_x, world_y, event)

    def _event_to_world(self, event: tk.Event) -> tuple[int, int]:
        """Convert a mouse event to world tile coordinates."""
        cx = self.map_canvas.canvasx(event.x)
        cy = self.map_canvas.canvasy(event.y)
        return self.canvas_to_world_x(cx), self.canvas_to_world_y(cy)

    # =========================================================================
    # Coordinate Conversion
    # =========================================================================

    def world_to_canvas_x(self, world_x: int) -> int:
        """Convert world tile X to canvas pixel X."""
        return (world_x + WORLD_OFFSET) * DISPLAY_SIZE

    def world_to_canvas_y(self, world_y: int) -> int:
        """Convert world tile Y to canvas pixel Y."""
        return (world_y + WORLD_OFFSET) * DISPLAY_SIZE

    def canvas_to_world_x(self, canvas_x: float) -> int:
        """Convert canvas pixel X to world tile X."""
        return int(canvas_x) // DISPLAY_SIZE - WORLD_OFFSET

    def canvas_to_world_y(self, canvas_y: float) -> int:
        """Convert canvas pixel Y to world tile Y."""
        return int(canvas_y) // DISPLAY_SIZE - WORLD_OFFSET

    def center_view_on(self, world_x: int, world_y: int) -> None:
        """Center the map view on a world coordinate."""
        canvas_x = self.world_to_canvas_x(world_x)
        canvas_y = self.world_to_canvas_y(world_y)

        total_size = WORLD_SIZE * DISPLAY_SIZE

        frac_x = canvas_x / total_size
        frac_y = canvas_y / total_size

        self.map_canvas.xview_moveto(max(0, frac_x - 0.1))
        self.map_canvas.yview_moveto(max(0, frac_y - 0.1))

    # =========================================================================
    # Map Grid
    # =========================================================================

    def _draw_map_grid(self) -> None:
        """Draw a subtle grid on the map canvas."""
        # Vertical lines
        for i in range(-GRID_RANGE, GRID_RANGE + 1):
            cx = self.world_to_canvas_x(i)
            cy_start = self.world_to_canvas_y(-GRID_RANGE)
            cy_end = self.world_to_canvas_y(GRID_RANGE)
            self.map_canvas.create_line(cx, cy_start, cx, cy_end, fill="#2a2a2a", tags="grid")

        # Horizontal lines
        for i in range(-GRID_RANGE, GRID_RANGE + 1):
            cy = self.world_to_canvas_y(i)
            cx_start = self.world_to_canvas_x(-GRID_RANGE)
            cx_end = self.world_to_canvas_x(GRID_RANGE)
            self.map_canvas.create_line(cx_start, cy, cx_end, cy, fill="#2a2a2a", tags="grid")

        # Origin crosshair (brighter)
        origin_x = self.world_to_canvas_x(0)
        origin_y = self.world_to_canvas_y(0)
        cy_start = self.world_to_canvas_y(-GRID_RANGE)
        cy_end = self.world_to_canvas_y(GRID_RANGE)
        cx_start = self.world_to_canvas_x(-GRID_RANGE)
        cx_end = self.world_to_canvas_x(GRID_RANGE)

        self.map_canvas.create_line(origin_x, cy_start, origin_x, cy_end, fill="#444", tags="grid")
        self.map_canvas.create_line(cx_start, origin_y, cx_end, origin_y, fill="#444", tags="grid")

    # =========================================================================
    # Atlas Loading
    # =========================================================================

    def _load_atlas(self) -> None:
        """Load a sprite atlas PNG and build tile index."""
        path = filedialog.askopenfilename(
            title="Select Sprite Atlas",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            img = Image.open(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            return

        # Validate atlas dimensions
        width, height = img.size
        if width != height:
            messagebox.showerror("Error", "Atlas must be square")
            return
        if width & (width - 1) != 0:
            messagebox.showerror("Error", "Atlas dimensions must be power of 2")
            return
        if width % SPRITE_SIZE != 0:
            messagebox.showerror("Error", f"Atlas size must be multiple of {SPRITE_SIZE}")
            return

        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Store atlas
        self.atlas_path = path
        self.atlas_image = img
        self.tile_images.clear()
        self.tile_pil_images.clear()

        # Extract tiles
        tiles_per_row = width // SPRITE_SIZE
        tile_count = tiles_per_row * tiles_per_row

        for idx in range(tile_count):
            tx = (idx % tiles_per_row) * SPRITE_SIZE
            ty = (idx // tiles_per_row) * SPRITE_SIZE

            tile_pil = img.crop((tx, ty, tx + SPRITE_SIZE, ty + SPRITE_SIZE))
            tile_scaled = tile_pil.resize((DISPLAY_SIZE, DISPLAY_SIZE), Image.NEAREST)
            tile_tk = ImageTk.PhotoImage(tile_scaled)

            self.tile_pil_images[idx] = tile_pil
            self.tile_images[idx] = tile_tk

        self.brush = 0
        self._rebuild_panel()
        self.update_status(f"Loaded atlas: {os.path.basename(path)} ({tile_count} tiles)")

    # =========================================================================
    # Map I/O
    # =========================================================================

    def _load_map(self) -> None:
        """Load a map file."""
        if not self.tile_images:
            messagebox.showwarning("Warning", "Load an atlas first")
            return

        path = filedialog.askopenfilename(
            title="Load Map",
            filetypes=[("Map files", "*.map"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            valid_indices = set(self.tile_images.keys())
            map_data = load_map(path, valid_indices)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            return

        # Update state
        self.tiles.clear()
        self.tiles.update(map_data.tiles)
        self.spawns.clear()
        self.spawns.update(map_data.spawns)

        # Redraw
        self._redraw_map_tiles()

        # Center view on map
        if self.tiles:
            min_x = min(x for x, y in self.tiles.keys())
            max_x = max(x for x, y in self.tiles.keys())
            min_y = min(y for x, y in self.tiles.keys())
            max_y = max(y for x, y in self.tiles.keys())
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            self.center_view_on(center_x, center_y)
        else:
            self.center_view_on(0, 0)

        tile_count = len(self.tiles)
        spawn_count = len(self.spawns)
        self.update_status(f"Loaded map: {map_data.name} ({tile_count} tiles, {spawn_count} spawns)")

    def _redraw_map_tiles(self) -> None:
        """Clear and redraw all tiles on the map canvas."""
        self.map_canvas.delete("maptile")

        for (x, y), tile in self.tiles.items():
            if tile.sprite in self.tile_images:
                px = self.world_to_canvas_x(x)
                py = self.world_to_canvas_y(y)
                self.map_canvas.create_image(
                    px, py,
                    anchor=tk.NW,
                    image=self.tile_images[tile.sprite],
                    tags=("maptile", f"maptile_{x}_{y}")
                )

    def _save_map(self) -> None:
        """Save the current map to a file."""
        if not self.tiles:
            messagebox.showwarning("Warning", "Map is empty, nothing to save")
            return

        path = filedialog.asksaveasfilename(
            title="Save Map",
            defaultextension=".map",
            filetypes=[("Map files", "*.map"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            save_map(path, self.tiles, self.spawns, self.atlas_path)

            # Calculate dimensions for status message
            min_x = min(x for x, y in self.tiles.keys())
            max_x = max(x for x, y in self.tiles.keys())
            min_y = min(y for x, y in self.tiles.keys())
            max_y = max(y for x, y in self.tiles.keys())
            width = max_x - min_x + 1
            height = max_y - min_y + 1

            spawn_count = len(self.spawns)
            self.update_status(
                f"Saved: {os.path.basename(path)} ({width}x{height}, {len(self.tiles)} tiles, {spawn_count} spawns)"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")