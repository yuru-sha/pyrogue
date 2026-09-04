"""Core package."""

from pyrogue.core.game_state import GameState

__all__ = ["Engine", "GameState"]


def __getattr__(name: str):
    """Load the TCOD engine lazily to keep core imports acyclic."""
    if name == "Engine":
        from pyrogue.core.engine import Engine

        return Engine
    raise AttributeError(name)
