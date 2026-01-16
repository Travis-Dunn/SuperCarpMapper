"""
MonsterSpawn data model.

Represents a spawn point for monsters on the map.
"""

from dataclasses import dataclass


@dataclass
class MonsterSpawn:
    """
    Represents a monster spawn point.

    Attributes:
        name: Monster definition name (references MonsterDefs in game).
        respawn_ticks: Game ticks until monster respawns after death.
    """
    name: str
    respawn_ticks: int = 100  # Default ~10 seconds at 10 ticks/sec