"""
Map file I/O operations.

File format:
    Header section (key:value pairs)
    ---
    Tile data (tab-delimited: x	y	sprite	blocked)
    --- examine
    Examine text (tab-delimited: x	y	text)
    --- <future sections>
    ...

To add a new tile attribute:
1. Add field to Tile dataclass in tile.py
2. Add _parse_<attr>_line() function
3. Add section handling in _parse_map_file()
4. Add _write_<attr>_section() function
5. Call _write_<attr>_section() in save_map()
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from mapper.tile import Tile

if TYPE_CHECKING:
    from typing import TextIO


class MapData:
    """Container for loaded map data."""

    def __init__(self) -> None:
        self.header: dict[str, str] = {}
        self.tiles: dict[tuple[int, int], Tile] = {}

    @property
    def name(self) -> str:
        return self.header.get("name", "Unknown")

    @property
    def tileset(self) -> str:
        return self.header.get("tileset", "unknown")


# =============================================================================
# Loading
# =============================================================================

def load_map(path: str, valid_sprite_indices: set[int]) -> MapData:
    """
    Load a map file from disk.

    Args:
        path: Path to the .map file.
        valid_sprite_indices: Set of valid sprite indices from loaded atlas.

    Returns:
        MapData containing header info and tiles.

    Raises:
        IOError: If file cannot be read.
        ValueError: If file format is invalid.
    """
    with open(path, "r") as f:
        return _parse_map_file(f, valid_sprite_indices)


def _parse_map_file(f: TextIO, valid_sprite_indices: set[int]) -> MapData:
    """Parse map file contents."""
    data = MapData()
    current_section: str | None = None  # None = header, "tiles" = main, or section name

    for line_num, line in enumerate(f, 1):
        line = line.rstrip("\n\r")

        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check for section delimiter
        if stripped.startswith("---"):
            if current_section is None:
                # End of header, start of tiles
                current_section = "tiles"
            else:
                # New named section
                section_name = stripped[3:].strip()
                current_section = section_name if section_name else "tiles"
            continue

        # Dispatch based on current section
        if current_section is None:
            _parse_header_line(stripped, data.header)
        elif current_section == "tiles":
            _parse_tile_line(line, line_num, valid_sprite_indices, data.tiles)
        elif current_section == "examine":
            _parse_examine_line(line, line_num, data.tiles)
        # Unknown sections are silently skipped (forward compatibility)

    return data


def _parse_header_line(line: str, header: dict[str, str]) -> None:
    """Parse a header line into key-value pair."""
    if ":" in line:
        key, value = line.split(":", 1)
        header[key.strip()] = value.strip()


def _parse_tile_line(
    line: str,
    line_num: int,
    valid_sprite_indices: set[int],
    tiles: dict[tuple[int, int], Tile]
) -> None:
    """
    Parse a tile line and add to tiles dict.

    Format: x	y	sprite	blocked (tab-delimited)
    """
    parts = line.split("\t")

    if len(parts) < 4:
        print(f"Warning line {line_num}: insufficient fields")
        return

    try:
        x = int(parts[0])
        y = int(parts[1])
        sprite = int(parts[2])
        blocked = bool(int(parts[3]))

        if sprite not in valid_sprite_indices:
            print(f"Warning line {line_num}: sprite index {sprite} not in loaded atlas")
            return

        tiles[(x, y)] = Tile(sprite=sprite, blocked=blocked)

    except ValueError as e:
        print(f"Warning line {line_num}: failed to parse tile: {e}")


def _parse_examine_line(
    line: str,
    line_num: int,
    tiles: dict[tuple[int, int], Tile]
) -> None:
    """
    Parse an examine text line and apply to existing tile.

    Format: x	y	examine_text (tab-delimited)
    """
    parts = line.split("\t", 2)  # Split into at most 3 parts

    if len(parts) < 3:
        print(f"Warning line {line_num}: insufficient fields in examine section")
        return

    try:
        x = int(parts[0])
        y = int(parts[1])
        examine_text = parts[2]

        coords = (x, y)
        if coords in tiles:
            tiles[coords].examine_text = examine_text if examine_text else None
        else:
            print(f"Warning line {line_num}: examine text for non-existent tile ({x}, {y})")

    except ValueError as e:
        print(f"Warning line {line_num}: failed to parse examine line: {e}")


# =============================================================================
# Saving
# =============================================================================

def save_map(
    path: str,
    tiles: dict[tuple[int, int], Tile],
    atlas_path: str | None
) -> None:
    """
    Save a map to disk.

    Args:
        path: Destination file path.
        tiles: Dictionary mapping (x, y) coordinates to Tiles.
        atlas_path: Path to the atlas file (for header metadata).

    Raises:
        IOError: If file cannot be written.
    """
    if not tiles:
        raise ValueError("Cannot save empty map")

    # Calculate bounds
    min_x = min(x for x, y in tiles.keys())
    max_x = max(x for x, y in tiles.keys())
    min_y = min(y for x, y in tiles.keys())
    max_y = max(y for x, y in tiles.keys())

    width = max_x - min_x + 1
    height = max_y - min_y + 1
    atlas_name = os.path.basename(atlas_path) if atlas_path else "unknown"

    with open(path, "w") as f:
        # Write header
        f.write("name:Untitled\n")
        f.write(f"width:{width}\n")
        f.write(f"height:{height}\n")
        f.write(f"origin:{min_x},{min_y}\n")
        f.write(f"tileset:{atlas_name}\n")
        f.write("---\n")

        # Write tiles
        for (x, y), tile in sorted(tiles.items()):
            f.write(_serialize_tile(x, y, tile))
            f.write("\n")

        # Write examine section (only if any tiles have examine text)
        _write_examine_section(f, tiles)


def _serialize_tile(x: int, y: int, tile: Tile) -> str:
    """
    Serialize a tile's core attributes.

    Format: x	y	sprite	blocked (tab-delimited)
    """
    blocked_flag = 1 if tile.blocked else 0
    return f"{x}\t{y}\t{tile.sprite}\t{blocked_flag}"


def _write_examine_section(f: TextIO, tiles: dict[tuple[int, int], Tile]) -> None:
    """Write the examine text section if any tiles have examine text."""
    examine_tiles = [
        (coords, tile) for coords, tile in tiles.items()
        if tile.examine_text is not None
    ]

    if not examine_tiles:
        return

    f.write("--- examine\n")
    for (x, y), tile in sorted(examine_tiles):
        f.write(f"{x}\t{y}\t{tile.examine_text}\n")