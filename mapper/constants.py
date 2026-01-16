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
