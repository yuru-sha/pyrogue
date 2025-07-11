"""
プレイヤーの移動処理を管理するマネージャー。

GameLogicから移動関連の処理を分離し、
より単純で保守しやすい構造にします。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext


class MovementManager:
    """
    プレイヤーの移動処理を担当するマネージャー。

    責務:
    - プレイヤーの移動可能性チェック
    - 状態異常による移動制限の処理
    - 混乱状態でのランダム移動
    - 移動後の処理調整
    """

    def __init__(self, context: GameContext) -> None:
        """
        MovementManagerを初期化。

        Args:
        ----
            context: 共有ゲームコンテキスト
        """
        self.context = context

    def handle_player_move(self, dx: int, dy: int) -> bool:
        """
        プレイヤーの移動処理。

        Args:
        ----
            dx: X方向の移動量
            dy: Y方向の移動量

        Returns:
        -------
            移動が成功した場合True
        """
        player = self.context.player

        # ターン管理から行動可能かチェック
        if not self.context.turn_manager.can_act(player):
            self.context.add_message("You are paralyzed and cannot move!")
            return False

        # 混乱状態のチェック
        if self.context.turn_manager.is_confused(player):
            # ランダムな方向に移動
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            self.context.add_message("You are confused and move randomly!")

        new_x = player.x + dx
        new_y = player.y + dy

        # 移動可能性チェック
        if not self._is_valid_move(new_x, new_y):
            return False

        # 移動先にモンスターがいるかチェック
        monster = self._get_monster_at_position(new_x, new_y)
        if monster:
            # 戦闘処理
            return self._handle_combat_movement(monster)

        # 実際の移動実行
        return self._execute_movement(new_x, new_y)

    def _is_valid_move(self, x: int, y: int) -> bool:
        """
        移動先が有効かチェック。

        Args:
        ----
            x: 移動先のX座標
            y: 移動先のY座標

        Returns:
        -------
            移動可能な場合True
        """
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        if not floor_data:
            return False

        # 境界チェック
        if not floor_data.is_valid_position(x, y):
            return False

        # 通行可能かチェック
        tile = floor_data.get_tile(x, y)
        if not tile.walkable:
            from pyrogue.map.tile import Door

            if isinstance(tile, Door):
                self.context.add_message("The door is closed. Press 'o' to open it.")
            else:
                self.context.add_message("You can't move there.")
            return False

        return True

    def _get_monster_at_position(self, x: int, y: int):
        """
        指定位置にいるモンスターを取得。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            モンスターインスタンス、いない場合None
        """
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        if not floor_data:
            return None

        # モンスターリストから該当位置のモンスターを探す
        for monster in floor_data.monsters:
            if monster.x == x and monster.y == y and monster.is_alive:
                return monster

        return None

    def _handle_combat_movement(self, monster) -> bool:
        """
        戦闘が発生する移動の処理。

        Args:
        ----
            monster: 戦闘対象のモンスター

        Returns:
        -------
            戦闘処理が成功した場合True
        """
        # 戦闘処理をCombatManagerに委譲
        combat_result = self.context.combat_manager.handle_player_attack(
            monster, self.context
        )

        if combat_result:
            # 戦闘成功時の処理
            return self._handle_post_combat_movement(monster)

        return False

    def _handle_post_combat_movement(self, monster) -> bool:
        """
        戦闘後の移動処理。

        Args:
        ----
            monster: 倒したモンスター

        Returns:
        -------
            処理が成功した場合True
        """
        # モンスターが死亡している場合、その位置に移動
        if not monster.is_alive:
            return self._execute_movement(monster.x, monster.y)

        # モンスターが生きている場合、移動しない
        return False

    def _execute_movement(self, new_x: int, new_y: int) -> bool:
        """
        実際の移動を実行。

        Args:
        ----
            new_x: 移動先のX座標
            new_y: 移動先のY座標

        Returns:
        -------
            移動が成功した場合True
        """
        # プレイヤーの位置を更新
        self.context.player.x = new_x
        self.context.player.y = new_y

        # 移動後の処理を実行
        self._handle_post_move_events()

        return True

    def _handle_post_move_events(self) -> None:
        """移動後に発生するイベントを処理。"""
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()

        if not floor_data:
            return

        # アイテムの取得チェック
        self._check_item_pickup()

        # 階段の処理
        self._check_stairs()

        # トラップの処理
        self._check_traps()

        # 特殊タイルの処理
        self._check_special_tiles()

    def _check_item_pickup(self) -> None:
        """プレイヤーの位置にアイテムがあるかチェック。"""
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        if not floor_data:
            return

        # プレイヤーの位置にあるアイテムを探す
        player = self.context.player
        items_at_position = [
            item
            for item in floor_data.items
            if item.x == player.x and item.y == player.y
        ]

        if not items_at_position:
            return

        # ゴールドのオートピックアップ処理
        gold_items = [
            item
            for item in items_at_position
            if hasattr(item, "item_type") and item.item_type == "GOLD"
        ]
        for gold_item in gold_items:
            amount = getattr(gold_item, "amount", 1)
            player.gold += amount
            floor_data.items.remove(gold_item)
            self.context.add_message(f"You picked up {amount} gold.")
            items_at_position.remove(gold_item)

        # 残りのアイテムがある場合は通知
        if items_at_position:
            if len(items_at_position) == 1:
                item = items_at_position[0]
                self.context.add_message(
                    f"You see a {item.name} here. Press 'g' to get it."
                )
            else:
                self.context.add_message(
                    f"You see {len(items_at_position)} items here. Press 'g' to get them."
                )

    def _check_stairs(self) -> None:
        """階段の処理。"""
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()

        if not floor_data:
            return

        tile = floor_data.get_tile(player.x, player.y)

        # 階段タイルの識別にisinstanceを使用
        from pyrogue.map.tile import StairsDown, StairsUp

        if isinstance(tile, StairsUp):
            self.context.add_message("You see stairs leading up. Press '<' to go up.")
        elif isinstance(tile, StairsDown):
            self.context.add_message(
                "You see stairs leading down. Press '>' to go down."
            )

    def _check_traps(self) -> None:
        """トラップの処理。"""
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()

        if not floor_data:
            return

        # トラップの発動チェック
        for trap in floor_data.traps:
            if (
                trap.x == player.x
                and trap.y == player.y
                and not getattr(trap, "is_triggered", False)
            ):
                trap.activate(self.context)

    def _check_special_tiles(self) -> None:
        """特殊タイルの処理。"""
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()

        if not floor_data:
            return

        tile = floor_data.get_tile(player.x, player.y)

        # 特殊タイルの効果を処理
        if hasattr(tile, "on_enter"):
            tile.on_enter(player, self.context)
