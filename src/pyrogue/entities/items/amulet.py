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
        ----
            context: 効果適用のためのコンテキスト

        Returns:
        -------
            効果の適用に成功したかどうか
        """
        # プレイヤーにアミュレット所持フラグを設定
        if hasattr(context, "player"):
            context.player.has_amulet = True
            context.add_message("The Amulet of Yendor glows with ancient power!")

            # B1F（地下1階）に地上への上り階段を生成
            self._create_escape_stairs(context)

            return True
        return False

    def _create_escape_stairs(self, context) -> None:
        """
        イェンダー取得時にB1Fに地上への上り階段を生成。

        Args:
        ----
            context: ゲームコンテキスト
        """
        try:
            # GameLogicまたはDungeonManagerへのアクセスを試行
            game_logic = None
            if hasattr(context, "game_logic"):
                game_logic = context.game_logic
            elif hasattr(context, "dungeon_manager"):
                game_logic = context

            if game_logic and hasattr(game_logic, "dungeon_manager"):
                dungeon_manager = game_logic.dungeon_manager

                # B1F（地下1階）のデータを取得
                b1f_data = dungeon_manager.get_floor(1)
                if b1f_data:
                    stairs_pos = self._place_escape_stairs_on_floor(b1f_data)
                    context.add_message("A magical staircase to the surface appears on the first floor!")

                    # 現在B1Fにいる場合は、階段の位置を知らせる
                    if dungeon_manager.current_floor == 1 and stairs_pos:
                        context.add_message(f"The escape stairs appear at ({stairs_pos[0]}, {stairs_pos[1]})")

        except Exception:
            # エラーが発生しても、アミュレット効果自体は成功扱い
            context.add_message("You sense the dungeon's structure shifting...")

    def _place_escape_stairs_on_floor(self, floor_data) -> tuple[int, int] | None:
        """
        指定されたフロアに脱出用の上り階段を配置。

        Args:
        ----
            floor_data: フロアデータ

        Returns:
        -------
            配置された階段の位置 (x, y)、配置に失敗した場合はNone
        """
        from pyrogue.map.tile import Floor, StairsUp

        # フロア内の適切な位置を探す
        tiles = floor_data.tiles
        height, width = tiles.shape

        # 床タイルの位置を探す
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if isinstance(tiles[y, x], Floor):
                    # 最初に見つかった床タイルに上り階段を配置
                    tiles[y, x] = StairsUp()
                    return (x, y)

        return None
