"""
Shared constants for the Mapper application.
"""

# Sprite dimensions
SPRITE_SIZE: int = 16
SCALE_FACTOR: int = 4
DISPLAY_SIZE: int = SPRITE_SIZE * SCALE_FACTOR  # 64 pixels on screen

# World coordinate system: centered on (0,0)
# Supports tiles from -WORLD_OFFSET to +WORLD_OFFSET-1 in each axis
WORLD_OFFSET: int = 512
WORLD_SIZE: int = WORLD_OFFSET * 2  # 1024 tiles total

# Grid display range (centered on origin)
GRID_RANGE: int = 64

# Fixed color palette (RGB tuples)
# Used for clear color and any other palette-based color selection
PALETTE: list[tuple[int, int, int]] = [
    (22, 13, 19),
    (49, 41, 62),
    (77, 102, 96),
    (149, 182, 102),
    (239, 158, 78),
    (173, 64, 48),
    (86, 33, 42),
    (144, 75, 65),
    (166, 153, 152),
    (95, 87, 94),
    (142, 184, 158),
    (246, 242, 195),
    (231, 155, 124),
    (155, 76, 99),
    (67, 33, 66),
    (209, 147, 95),
]