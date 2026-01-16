"""
Editor modes package.

Each mode handles editing of a specific tile attribute.
"""

from mapper.modes.base import EditorMode
from mapper.modes.blocked import BlockedMode
from mapper.modes.examine import ExamineMode
from mapper.modes.paint import PaintTileMode

__all__ = [
    "EditorMode",
    "PaintTileMode",
    "BlockedMode",
    "ExamineMode",
]