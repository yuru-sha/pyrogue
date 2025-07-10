"""
Amulet of Yendor アイテムモジュール。

オリジナルRogueのゲーム目標となる重要なアイテムです。
"""

from __future__ import annotations

from pyrogue.entities.items.item import Item


class AmuletOfYendor(Item):
    """Amulet of Yendor クラス"""

    def __init__(self, x: int, y: int):
        super().__init__(
            x=x,
            y=y,
            name="Amulet of Yendor",
            char="*",
            color=(255, 215, 0),  # 金色
            stackable=False,
            identified=True,
        )

    def pick_up(self) -> str:
        """アミュレットを拾った時のメッセージ"""
        return "You have found the Amulet of Yendor! Now escape to the surface!"

    def apply_effect(self, context) -> bool:
        """
        アミュレットの効果を適用

        Args:
            context: 効果適用のためのコンテキスト

        Returns:
            効果の適用に成功したかどうか
        """
        # プレイヤーにアミュレット所持フラグを設定
        if hasattr(context, 'player'):
            context.player.has_amulet = True
            context.add_message("The Amulet of Yendor glows with ancient power!")
            return True
        return False
