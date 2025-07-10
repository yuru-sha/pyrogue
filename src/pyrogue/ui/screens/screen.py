"""Screen base module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.event
from tcod.console import Console

if TYPE_CHECKING:
    from pyrogue.core.engine import Engine


class Screen:
    """画面の基本クラス"""

    def __init__(self, engine: Engine) -> None:
        """
        スクリーンを初期化。

        Args:
            engine: メインゲームエンジンのインスタンス

        """
        self.engine = engine

    def render(self, console: Console) -> None:
        """
        画面を描画

        Args:
            console: 描画対象のコンソール

        """
        raise NotImplementedError

    def handle_key(self, key: tcod.event.KeyDown) -> Screen | None:
        """
        キー入力を処理

        Args:
            key: キー入力イベント

        Returns:
            Optional[Screen]: 次の画面（Noneの場合は現在の画面を維持）

        """
        raise NotImplementedError
