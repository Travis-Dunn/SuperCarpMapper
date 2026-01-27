"""
Tile defaults loader.

Loads per-sprite default values (blocked, examine text) from a companion
file that lives next to the atlas PNG.

File format (.tiles):
    # Comments start with #
    # Format: index <tab> blocked (0/1) <tab> examine text
    # Only list tiles that need non-default values
    
    0	0	Grass
    15	1	A stone wall
    32	0	A sealed wooden barrel
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class TileDefaults:
    """Default values for a tile sprite."""
    blocked: bool = False
    examine_text: str | None = None


def get_defaults_path(atlas_path: str) -> str:
    """Get the expected path for a tile defaults file given an atlas path."""
    base, _ = os.path.splitext(atlas_path)
    return base + ".tiles"


def load_tile_defaults(atlas_path: str) -> dict[int, TileDefaults]:
    """
    Load tile defaults from a companion file.

    Looks for a .tiles file next to the atlas PNG (e.g., terrain.png -> terrain.tiles).

    Args:
        atlas_path: Path to the atlas PNG file.

    Returns:
        Dictionary mapping sprite index to TileDefaults.
        Returns empty dict if companion file doesn't exist.
    """
    tiles_path = get_defaults_path(atlas_path)

    if not os.path.exists(tiles_path):
        return {}

    defaults: dict[int, TileDefaults] = {}

    with open(tiles_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip("\n\r")

            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Parse tab-delimited: index, blocked, examine_text
            parts = line.split("\t")

            if len(parts) < 2:
                print(f"Warning {tiles_path}:{line_num}: insufficient fields")
                continue

            try:
                index = int(parts[0])
                blocked = bool(int(parts[1]))
                examine_text = parts[2] if len(parts) > 2 and parts[2] else None

                defaults[index] = TileDefaults(
                    blocked=blocked,
                    examine_text=examine_text
                )
            except ValueError as e:
                print(f"Warning {tiles_path}:{line_num}: failed to parse: {e}")

    return defaults
