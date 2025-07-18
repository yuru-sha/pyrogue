"""
自動探索コマンドハンドラーモジュール。

自動探索機能に関するコマンド処理を専門に担当します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogue.core.command_handler import CommandResult

if TYPE_CHECKING:
    from pyrogue.core.command_handler import CommandContext


class AutoExploreHandler:
    """自動探索コマンド専用のハンドラー。"""

    def __init__(self, context: CommandContext):
        self.context = context

    def handle_auto_explore(self) -> CommandResult:
        """自動探索コマンドの処理。"""
        try:
            player = self.context.player
            game_logic = self.context.game_logic
            current_floor = game_logic.get_current_floor_data()

            if not current_floor:
                self.context.add_message("Cannot auto-explore: no floor data available.")
                return CommandResult(False)

            # 敵が近くにいる場合は自動探索を停止
            nearby_enemies = self._check_nearby_enemies(current_floor, player)
            if nearby_enemies:
                self.context.add_message(f"Auto-explore stopped: {nearby_enemies[0].name} nearby!")
                return CommandResult(False)

            # 未探索エリアを探す
            target_pos = self._find_nearest_unexplored_area(current_floor, player)

            if target_pos is None:
                self.context.add_message("Auto-explore complete: all areas explored.")
                return CommandResult(True)

            # 目標地点への次の一歩を計算
            next_move = self._calculate_next_move(current_floor, player, target_pos)

            if next_move is None:
                self.context.add_message("Auto-explore stopped: no safe path found.")
                return CommandResult(False)

            # 移動を実行
            dx, dy = next_move
            success = game_logic.handle_player_move(dx, dy)

            if success:
                self.context.add_message(f"Auto-exploring... (target: {target_pos[0]}, {target_pos[1]})")
                return CommandResult(True, should_end_turn=True)
            self.context.add_message("Auto-explore stopped: movement blocked.")
            return CommandResult(False)

        except Exception as e:
            self.context.add_message(f"Auto-explore error: {e}")
            return CommandResult(False)

    def _check_nearby_enemies(self, current_floor, player) -> list:
        """プレイヤー周囲の敵をチェック。"""
        nearby_enemies = []

        for monster in current_floor.monster_spawner.monsters:
            distance = abs(monster.x - player.x) + abs(monster.y - player.y)
            if distance <= 3:  # 3マス以内
                nearby_enemies.append(monster)

        return nearby_enemies

    def _find_nearest_unexplored_area(self, current_floor, player) -> tuple[int, int] | None:
        """最も近い未探索エリアを見つける。"""
        from pyrogue.map.tile import Floor

        explored = current_floor.explored
        tiles = current_floor.tiles
        player_pos = (player.x, player.y)

        min_distance = float("inf")
        target_pos = None

        # 探索済みエリアの境界付近で未探索の床タイルを探す
        for y in range(1, tiles.shape[0] - 1):
            for x in range(1, tiles.shape[1] - 1):
                # 未探索の床タイルかチェック
                if not explored[y, x] and isinstance(tiles[y, x], Floor):
                    # 隣接する探索済みエリアがあるかチェック
                    has_explored_neighbor = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < explored.shape[0] and 0 <= nx < explored.shape[1] and explored[ny, nx]:
                                has_explored_neighbor = True
                                break
                        if has_explored_neighbor:
                            break

                    # 探索境界の未探索エリアを優先
                    if has_explored_neighbor:
                        distance = abs(x - player_pos[0]) + abs(y - player_pos[1])
                        if distance < min_distance:
                            min_distance = distance
                            target_pos = (x, y)

        return target_pos

    def _calculate_next_move(self, current_floor, player, target_pos) -> tuple[int, int] | None:
        """目標地点への次の移動を計算（簡易A*アルゴリズム）。"""
        from pyrogue.map.tile import Door, Floor

        tiles = current_floor.tiles
        target_x, target_y = target_pos

        # 目標への大まかな方向を計算
        dx = 0
        dy = 0

        if target_x > player.x:
            dx = 1
        elif target_x < player.x:
            dx = -1

        if target_y > player.y:
            dy = 1
        elif target_y < player.y:
            dy = -1

        # 候補移動方向のリスト（優先順位付き）
        moves = []

        # 直接的な移動を最優先
        if dx != 0 or dy != 0:
            moves.append((dx, dy))

        # 斜め移動が不可能な場合の代替案
        if dx != 0:
            moves.append((dx, 0))
        if dy != 0:
            moves.append((0, dy))

        # 各移動候補をチェック
        for move_dx, move_dy in moves:
            new_x = player.x + move_dx
            new_y = player.y + move_dy

            # 境界チェック
            if new_x < 0 or new_x >= tiles.shape[1] or new_y < 0 or new_y >= tiles.shape[0]:
                continue

            # タイルの通行可能性をチェック
            tile = tiles[new_y, new_x]
            if isinstance(tile, (Floor, Door)):
                # 扉の場合は開いているかチェック
                if isinstance(tile, Door) and not tile.is_open:
                    continue

                # モンスターがいないかチェック
                monster_at_pos = current_floor.monster_spawner.get_monster_at(new_x, new_y)
                if monster_at_pos is None:
                    return (move_dx, move_dy)

        return None
