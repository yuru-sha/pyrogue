"""Screen base module."""

from __future__ import annotations

import tcod.event
from tcod.console import Console


class Screen:
    """画面の基本クラス"""

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
