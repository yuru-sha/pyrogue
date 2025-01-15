"""Main entry point for the game."""

import sys
import traceback
from pathlib import Path

from pyrogue.core import Engine
from pyrogue.utils import game_logger

def main() -> None:
    """Main entry point for the game."""
    try:
        # Create data directories if they don't exist
        data_dir = Path("data")
        fonts_dir = data_dir / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)

        # Initialize and run the game
        engine = Engine()
        engine.initialize()
        engine.run()

    except Exception as e:
        game_logger.error(
            "Fatal error occurred",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
