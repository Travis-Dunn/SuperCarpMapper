"""
Character data model.

Represents an NPC placement on the map.
"""

from dataclasses import dataclass


@dataclass
class Character:
    """
    Represents an NPC placement.

    Attributes:
        name: Character definition name (references CharacterDefs in game).
    """
    name: str