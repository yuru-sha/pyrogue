"""
メインモジュール。

このモジュールは、PyRogueゲームのエントリーポイントを提供します。
ゲームエンジンの初期化、実行、エラーハンドリングを担当し、
安全なゲームの起動と終了を保証します。

Example:
    $ python -m pyrogue.main

"""

import sys
import traceback

from pyrogue.core.engine import Engine
from pyrogue.utils import game_logger


def main() -> None:
    """
    メイン関数。

    ゲームエンジンを初期化し、メインゲームループを開始します。
    例外が発生した場合は適切にログ記録し、エラーメッセージを
    標準エラー出力に表示してプログラムを終了します。
    """
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
