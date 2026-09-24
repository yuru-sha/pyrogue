"""Display-only field-of-view override for the canonical game state."""

from __future__ import annotations


class FOVManager:
    """Toggle between normal visibility and showing every map cell."""

    def __init__(self, game_screen) -> None:
        self.game_screen = game_screen
        self.fov_enabled = True

    def toggle_fov(self) -> str:
        """Toggle the display-only visibility override."""
        self.fov_enabled = not self.fov_enabled
        return "FOV enabled" if self.fov_enabled else "FOV disabled"
