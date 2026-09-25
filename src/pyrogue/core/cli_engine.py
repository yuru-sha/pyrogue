"""CLI adapter for the canonical game state."""

from __future__ import annotations

from pyrogue.core.rogue_game import GameState, GameStatus
from pyrogue.core.save_manager import SaveManager
from pyrogue.presentation.display_renderer import render_ascii


class CLIEngine:
    """Run the shared GameState command API in a terminal."""

    def __init__(self, seed: int | None = None) -> None:
        self.game_state = GameState(seed)
        self.running = False

    def run(self) -> None:
        """Read and execute commands until the game ends or input closes."""
        self.running = True
        print("PyRogue CLI Mode - Type '?' for help")
        self.display_game_state()
        while self.running:
            try:
                command = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break
            if command:
                self.process_command(command)

    def process_command(self, command: str) -> bool:
        """Execute one canonical game command and print its result."""
        parts = command.split()
        if not parts:
            return True

        raw_command = parts[0]
        game_command = raw_command if len(raw_command) == 1 or raw_command[0].isdigit() else raw_command.lower()
        args = parts[1:]

        if game_command.lower() == "load":
            save_manager = SaveManager()
            data = save_manager.load_game_state()
            if data is None:
                if save_manager.last_error is None:
                    print("No compatible save file found.")
                else:
                    print(f"Failed to load save data: {save_manager.last_error}")
                return True
            try:
                self.game_state = GameState.from_dict(data)
                print("Game loaded successfully.")
            except (TypeError, ValueError):
                print("Save file is not compatible with PyRogue 0.3.1.")
                return True
            self.display_game_state()
            return True

        if game_command in {"S", "save"}:
            result = self.game_state.execute("save")
            if result.success and SaveManager().save_game_state(self.game_state.to_dict()):
                print("Game saved successfully.")
            else:
                print("Failed to save game.")
            return True

        result = self.game_state.execute(game_command, args)
        if result.message:
            print(result.message)
        if result.success:
            self.display_game_state()

        if result.state == GameStatus.DEAD:
            summary = SaveManager().finalize_death(self.game_state)
            if summary is not None:
                print("GAME OVER")
                print(f"Score: {summary['score']}")
                print(f"Deepest floor: B{summary['deepest_floor']}F")
                print(f"Cause: {summary['cause']}")
        elif result.state == GameStatus.VICTORY:
            summary = result.data or self.game_state.victory_summary
            print("VICTORY!")
            print(f"Score: {summary['score']}")
            print(f"Deepest floor: B{summary['deepest_floor']}F")

        if result.state in {GameStatus.QUIT, GameStatus.DEAD, GameStatus.VICTORY}:
            self.running = False
        return True

    def display_game_state(self) -> None:
        """Print the canonical map and player status."""
        print(render_ascii(self.game_state.display_cells(), self.game_state.width, self.game_state.height))
        print(self.game_state.status_text())
