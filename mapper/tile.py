"""
Tile data model.

All per-tile attributes are defined here. To add a new attribute:
1. Add the field to the Tile dataclass (with a default value)
2. Update map_io.py to serialize/deserialize it
3. Create a mode in modes/ to edit it
"""

from dataclasses import dataclass


@dataclass
class Tile:
    """
    Represents a single map tile and all its attributes.

    Attributes:
        sprite: Index into the sprite atlas.
        blocked: Whether the tile blocks movement.
        examine_text: Text displayed when player examines this tile (max 80 chars).
    """
    sprite: int
    blocked: bool = False
    examine_text: str | None = None