"""Main module."""

import sys
import traceback

from pyrogue.core.engine import Engine
from pyrogue.utils import game_logger


def main() -> None:
    """Main function."""
    try:
        engine = Engine()
        engine.initialize()
        engine.run()
    except Exception as e:
        game_logger.error(
            "Fatal error", extra={"error": str(e), "traceback": traceback.format_exc()}
        )
        print(f"Error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
