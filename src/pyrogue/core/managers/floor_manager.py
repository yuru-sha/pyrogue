"""
フロア・階層管理を担当するマネージャー。

GameLogicから階層関連の処理を分離し、
より単純で保守しやすい構造にします。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext


class FloorManager:
    """
    フロア・階層管理を担当するマネージャー。
    
    責務:
    - 階段の上り下り処理
    - フロア間の移動処理
    - フロア固有の処理
    - 扉の開閉処理
    """

    def __init__(self, context: GameContext) -> None:
        """
        FloorManagerを初期化。
        
        Args:
            context: 共有ゲームコンテキスト
        """
        self.context = context

    def handle_stairs_up(self) -> bool:
        """
        階段を上る処理。
        
        Returns:
            階段を上ることができた場合True
        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            self.context.add_message("You can't go up here.")
            return False
        
        # プレイヤーの位置に上り階段があるかチェック
        tile = floor_data.get_tile(player.x, player.y)
        from pyrogue.map.tile import StairsUp
        if not isinstance(tile, StairsUp):
            self.context.add_message("There are no stairs up here.")
            return False
        
        # 1階の場合は地上に出る
        current_floor = self.context.dungeon_manager.current_floor
        if current_floor <= 1:
            # 勝利条件チェック
            if getattr(self.context.player, 'has_amulet', False):
                self.context.add_message("You have escaped with the Amulet of Yendor! You win!")
                self._handle_victory()
            else:
                self.context.add_message("You climb up the stairs and emerge from the dungeon!")
                self._handle_dungeon_exit()
            return True
        
        # 上の階に移動
        return self._move_to_floor(current_floor - 1, "up")

    def handle_stairs_down(self) -> bool:
        """
        階段を下る処理。
        
        Returns:
            階段を下ることができた場合True
        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            self.context.add_message("You can't go down here.")
            return False
        
        # プレイヤーの位置に下り階段があるかチェック
        tile = floor_data.get_tile(player.x, player.y)
        from pyrogue.map.tile import StairsDown
        if not isinstance(tile, StairsDown):
            self.context.add_message("There are no stairs down here.")
            return False
        
        # 最下階の場合は処理を制限
        current_floor = self.context.dungeon_manager.current_floor
        max_floor = 26  # オリジナルRogue準拠
        
        if current_floor >= max_floor:
            self.context.add_message("You can't go any deeper.")
            return False
        
        # 下の階に移動
        return self._move_to_floor(current_floor + 1, "down")

    def _move_to_floor(self, target_floor: int, direction: str) -> bool:
        """
        指定フロアに移動。
        
        Args:
            target_floor: 移動先のフロア番号
            direction: 移動方向（"up" または "down"）
            
        Returns:
            移動が成功した場合True
        """
        try:
            # フロアを変更
            self.context.dungeon_manager.set_current_floor(target_floor)
            
            # 新しいフロアのデータを取得
            new_floor_data = self.context.dungeon_manager.get_current_floor_data()
            
            if not new_floor_data:
                self.context.add_message("Failed to generate the new floor.")
                return False
            
            # プレイヤーの位置を設定
            self._set_player_position_on_new_floor(new_floor_data, direction)
            
            # フロア移動メッセージ
            if direction == "up":
                self.context.add_message(f"You ascend to floor {target_floor}.")
            else:
                self.context.add_message(f"You descend to floor {target_floor}.")
            
            # フロア移動後の処理
            self._handle_post_floor_change(target_floor)
            
            return True
            
        except Exception as e:
            self.context.add_message(f"Failed to move to floor {target_floor}: {str(e)}")
            return False

    def _set_player_position_on_new_floor(self, floor_data, direction: str) -> None:
        """
        新しいフロアでのプレイヤー位置を設定。
        
        Args:
            floor_data: 新しいフロアのデータ
            direction: 移動方向（"up" または "down"）
        """
        player = self.context.player
        
        if direction == "up":
            # 上に移動する場合は下り階段の位置に配置
            stairs_down_pos = floor_data.get_stairs_down_position()
            if stairs_down_pos:
                player.x, player.y = stairs_down_pos
            else:
                player.x, player.y = floor_data.start_pos
        else:
            # 下に移動する場合は上り階段の位置に配置
            stairs_up_pos = floor_data.get_stairs_up_position()
            if stairs_up_pos:
                player.x, player.y = stairs_up_pos
            else:
                player.x, player.y = floor_data.start_pos

    def _handle_post_floor_change(self, new_floor: int) -> None:
        """
        フロア変更後の処理。
        
        Args:
            new_floor: 新しいフロア番号
        """
        # 視界を更新
        self._update_fov()
        
        # フロア固有の処理
        self._handle_floor_specific_events(new_floor)
        
        # モンスターAIの更新
        if hasattr(self.context, 'monster_ai_manager'):
            self.context.monster_ai_manager.update_floor_context()

    def _update_fov(self) -> None:
        """視界を更新。"""
        if hasattr(self.context, 'game_screen') and self.context.game_screen:
            self.context.game_screen.update_fov()

    def _handle_floor_specific_events(self, floor_number: int) -> None:
        """
        フロア固有のイベントを処理。
        
        Args:
            floor_number: フロア番号
        """
        # 特定フロアでの特別な処理
        if floor_number == 26:
            # 最下階の処理
            self.context.add_message("You sense something powerful in the depths...")
        elif floor_number % 5 == 0:
            # 5の倍数階での処理
            self.context.add_message("You feel the air grow heavier...")

    def _handle_victory(self) -> None:
        """勝利時の処理。"""
        # スコア計算
        if hasattr(self.context, 'score_manager'):
            final_score = self.context.score_manager.calculate_final_score()
            self.context.add_message(f"Final Score: {final_score}")
        
        # 勝利フラグの設定
        if hasattr(self.context, 'game_logic'):
            self.context.game_logic.game_won = True
        
        # 勝利記録
        self.context.add_message("Congratulations! You have completed PyRogue!")

    def _handle_dungeon_exit(self) -> None:
        """ダンジョン脱出時の処理。"""
        # スコア計算
        if hasattr(self.context, 'score_manager'):
            final_score = self.context.score_manager.calculate_final_score()
            self.context.add_message(f"Final Score: {final_score}")
        
        # 脱出フラグの設定
        if hasattr(self.context, 'game_logic'):
            self.context.game_logic.game_won = True

    def handle_open_door(self) -> bool:
        """
        扉を開く処理。
        
        Returns:
            扉を開くことができた場合True
        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            self.context.add_message("No doors to open here.")
            return False
        
        # プレイヤーの周囲8方向をチェック
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                x, y = player.x + dx, player.y + dy
                
                if floor_data.is_valid_position(x, y):
                    tile = floor_data.get_tile(x, y)
                    
                    from pyrogue.map.tile import Door
                    if isinstance(tile, Door) and not tile.walkable:
                        # 扉を開く
                        floor_data.set_tile_walkable(x, y, True)
                        self.context.add_message("You open the door.")
                        return True
        
        self.context.add_message("No doors to open here.")
        return False

    def handle_close_door(self) -> bool:
        """
        扉を閉じる処理。
        
        Returns:
            扉を閉じることができた場合True
        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            self.context.add_message("No doors to close here.")
            return False
        
        # プレイヤーの周囲8方向をチェック
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                x, y = player.x + dx, player.y + dy
                
                if floor_data.is_valid_position(x, y):
                    tile = floor_data.get_tile(x, y)
                    
                    from pyrogue.map.tile import Door
                    if isinstance(tile, Door) and tile.walkable:
                        # 扉の位置にモンスターがいないかチェック
                        if self._is_position_occupied(x, y):
                            self.context.add_message("There is someone in the way.")
                            continue
                        
                        # 扉を閉じる
                        floor_data.set_tile_walkable(x, y, False)
                        self.context.add_message("You close the door.")
                        return True
        
        self.context.add_message("No doors to close here.")
        return False

    def _is_position_occupied(self, x: int, y: int) -> bool:
        """
        指定位置にモンスターがいるかチェック。
        
        Args:
            x: X座標
            y: Y座標
            
        Returns:
            モンスターがいる場合True
        """
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            return False
        
        # モンスターがその位置にいるかチェック
        for monster in floor_data.monsters:
            if monster.x == x and monster.y == y and monster.is_alive:
                return True
        
        return False

    def handle_search(self) -> bool:
        """
        隠し扉・トラップの探索処理。
        
        Returns:
            何かを発見した場合True
        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            self.context.add_message("Nothing to search here.")
            return False
        
        found_something = False
        
        # プレイヤーの周囲をチェック
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                x, y = player.x + dx, player.y + dy
                
                if floor_data.is_valid_position(x, y):
                    # 隠し扉の発見
                    if self._find_secret_door(x, y):
                        found_something = True
                    
                    # トラップの発見
                    if self._find_trap(x, y):
                        found_something = True
        
        if not found_something:
            self.context.add_message("You don't find anything.")
        
        return found_something

    def _find_secret_door(self, x: int, y: int) -> bool:
        """
        隠し扉を発見。
        
        Args:
            x: X座標
            y: Y座標
            
        Returns:
            隠し扉を発見した場合True
        """
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            return False
        
        # 隠し扉の判定ロジック（実装に依存）
        # 暫定的に確率的な発見とする
        import random
        
        tile = floor_data.get_tile(x, y)
        from pyrogue.map.tile import Wall
        if isinstance(tile, Wall) and random.random() < 0.1:  # 10%の確率
            # 隠し扉を通常の扉に変更
            floor_data.set_tile(x, y, "Door")
            self.context.add_message("You found a secret door!")
            return True
        
        return False

    def _find_trap(self, x: int, y: int) -> bool:
        """
        トラップを発見。
        
        Args:
            x: X座標
            y: Y座標
            
        Returns:
            トラップを発見した場合True
        """
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            return False
        
        # その位置にあるトラップを探す
        for trap in floor_data.traps:
            if trap.x == x and trap.y == y and not trap.is_discovered:
                trap.discover()
                self.context.add_message(f"You found a {trap.name}!")
                return True
        
        return False

    def handle_disarm_trap(self) -> bool:
        """
        トラップの解除処理。
        
        Returns:
            トラップを解除できた場合True
        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()
        
        if not floor_data:
            self.context.add_message("No traps to disarm here.")
            return False
        
        # プレイヤーの周囲のトラップをチェック
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                x, y = player.x + dx, player.y + dy
                
                if floor_data.is_valid_position(x, y):
                    for trap in floor_data.traps:
                        if trap.x == x and trap.y == y and trap.is_discovered:
                            # トラップの解除を試行
                            if trap.disarm(player):
                                self.context.add_message(f"You successfully disarm the {trap.name}.")
                                return True
                            else:
                                self.context.add_message(f"You fail to disarm the {trap.name}.")
                                return False
        
        self.context.add_message("No traps to disarm here.")
        return False