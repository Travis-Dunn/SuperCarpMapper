"""
Editor modes package.

Each mode handles editing of a specific tile attribute.
"""

from mapper.modes.base import EditorMode
from mapper.modes.blocked import BlockedMode
from mapper.modes.character import CharacterMode
from mapper.modes.examine import ExamineMode
from mapper.modes.paint import PaintTileMode
from mapper.modes.spawn import SpawnMode

__all__ = [
    "EditorMode",
    "PaintTileMode",
    "BlockedMode",
    "ExamineMode",
    "SpawnMode",
    "CharacterMode",
]