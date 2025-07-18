"""
モンスター戦闘管理コンポーネント。

このモジュールは、モンスターの戦闘行動と特殊攻撃を管理します。
攻撃判定、特殊能力、戦闘効果を担当します。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from pyrogue.constants import CombatConstants, ProbabilityConstants
from pyrogue.utils import game_logger

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext
    from pyrogue.entities.actors.monster import Monster


class MonsterCombatManager:
    """
    モンスター戦闘システムの管理クラス。

    モンスターの攻撃行動、特殊能力、戦闘効果を管理し、
    プレイヤーとの戦闘を処理します。
    """

    def __init__(self) -> None:
        """モンスター戦闘マネージャーを初期化。"""

    def can_use_ranged_attack(self, monster: Monster, player) -> bool:
        """
        遠距離攻撃が使用可能かチェック。

        Args:
        ----
            monster: チェック対象のモンスター
            player: プレイヤー

        Returns:
        -------
            遠距離攻撃可能な場合True

        """
        if not hasattr(monster, "can_ranged_attack") or not monster.can_ranged_attack:
            return False

        if hasattr(monster, "special_ability_cooldown") and monster.special_ability_cooldown > 0:
            return False

        distance = self._calculate_distance(monster.x, monster.y, player.x, player.y)
        ranged_range = getattr(monster, "ranged_attack_range", 5)

        # 射程内かつ隣接していない場合
        return CombatConstants.ADJACENT_DISTANCE_THRESHOLD < distance <= ranged_range

    def use_ranged_attack(self, monster: Monster, player, context: GameContext) -> None:
        """
        遠距離攻撃を実行。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        damage = getattr(monster, "ranged_attack_damage", monster.attack // 2)

        # 攻撃命中判定
        if random.random() < ProbabilityConstants.MONSTER_RANGED_ATTACK_HIT_RATE:  # 80%の命中率
            actual_damage = max(1, damage - player.get_defense())
            player.take_damage(actual_damage, context)
            context.add_message(f"{monster.name} shoots you for {actual_damage} damage!")
        else:
            context.add_message(f"{monster.name}'s ranged attack misses!")

        # クールダウン設定
        monster.special_ability_cooldown = 3

        game_logger.debug(f"{monster.name} used ranged attack on player")

    def can_use_special_attack(self, monster: Monster) -> bool:
        """
        特殊攻撃が使用可能かチェック。

        Args:
        ----
            monster: チェック対象のモンスター

        Returns:
        -------
            特殊攻撃可能な場合True

        """
        if hasattr(monster, "special_ability_cooldown") and monster.special_ability_cooldown > 0:
            return False

        # 30%の確率で特殊攻撃を使用
        return random.random() < ProbabilityConstants.MONSTER_SPECIAL_ATTACK_CHANCE and (
            getattr(monster, "can_steal_items", False)
            or getattr(monster, "can_steal_gold", False)
            or getattr(monster, "can_drain_level", False)
        )

    def use_special_attack(self, monster: Monster, player, context: GameContext) -> None:
        """
        特殊攻撃を実行。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        # アイテム盗取
        if getattr(monster, "can_steal_items", False):
            self._steal_item(monster, player, context)
        # ゴールド盗取
        elif getattr(monster, "can_steal_gold", False):
            self._steal_gold(monster, player, context)
        # レベル下げ攻撃
        elif getattr(monster, "can_drain_level", False):
            self._drain_level(monster, player, context)
        else:
            # 通常攻撃にフォールバック
            self._monster_attack_player(monster, context)

        # クールダウン設定
        monster.special_ability_cooldown = 5

    def _steal_item(self, monster: Monster, player, context: GameContext) -> None:
        """
        アイテム盗取攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        # インベントリからランダムなアイテムを盗む
        items = player.inventory.items
        if items:
            stolen_item = random.choice(items)

            # スタック可能アイテムの場合は1個だけ盗む
            if stolen_item.stackable and stolen_item.stack_count > 1:
                player.inventory.remove_item(stolen_item, 1)
                context.add_message(f"{monster.name} steals one {stolen_item.name}!")
                game_logger.debug(f"{monster.name} stole 1 {stolen_item.name} from player")
            else:
                player.inventory.remove_item(stolen_item)
                context.add_message(f"{monster.name} steals your {stolen_item.name}!")
                game_logger.debug(f"{monster.name} stole {stolen_item.name} from player")

            # モンスターが逃走を開始
            monster.is_fleeing = True
        else:
            context.add_message(f"{monster.name} tries to steal from you, but you have nothing!")

    def _steal_gold(self, monster: Monster, player, context: GameContext) -> None:
        """
        ゴールド盗取攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        if player.gold > 0:
            stolen_amount = min(player.gold, random.randint(10, 50))
            player.gold -= stolen_amount
            context.add_message(f"{monster.name} steals {stolen_amount} gold from you!")

            # モンスターが逃走を開始
            monster.is_fleeing = True

            game_logger.debug(f"{monster.name} stole {stolen_amount} gold from player")
        else:
            context.add_message(f"{monster.name} searches for gold, but you have none!")

    def _drain_level(self, monster: Monster, player, context: GameContext) -> None:
        """
        レベル下げ攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            player: プレイヤー
            context: ゲームコンテキスト

        """
        if player.level > 1:
            # レベルを1下げる
            player.level -= 1

            # ステータスも減少
            player.max_hp = max(10, player.max_hp - 5)
            player.hp = min(player.hp, player.max_hp)
            player.attack = max(1, player.attack - 2)
            player.defense = max(0, player.defense - 1)

            context.add_message(f"{monster.name} drains your life force! You feel weaker!")
            game_logger.debug(f"{monster.name} drained player level from {player.level + 1} to {player.level}")
        else:
            # 通常ダメージを与える
            damage = max(1, monster.attack - player.get_defense())
            player.take_damage(damage, context)
            context.add_message(f"{monster.name} attacks you for {damage} damage!")

    def _monster_attack_player(self, monster: Monster, context: GameContext) -> None:
        """
        モンスターがプレイヤーを攻撃。

        Args:
        ----
            monster: 攻撃するモンスター
            context: ゲームコンテキスト

        """
        # 戦闘処理はCombatManagerに委譲
        # ここではAIの観点での攻撃決定のみ
        game_logger.debug(f"{monster.name} attacks player")

    def split_monster_on_damage(self, monster: Monster, context: GameContext) -> None:
        """
        ダメージを受けた時のモンスター分裂処理。

        Args:
        ----
            monster: 分裂するモンスター
            context: ゲームコンテキスト

        """
        if not getattr(monster, "can_split", False):
            return

        # 既に分裂している場合はスキップ
        if getattr(monster, "parent_monster", None) is not None:
            return

        # 分裂判定（30%の確率）
        if random.random() > ProbabilityConstants.MONSTER_SPLIT_CHANCE:
            return

        floor_data = context.get_current_floor_data()
        if not floor_data or not hasattr(floor_data, "monster_spawner"):
            return

        # 分裂先の座標を探す
        spawn_positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                new_x = monster.x + dx
                new_y = monster.y + dy

                if self._can_monster_move_to(new_x, new_y, context):
                    spawn_positions.append((new_x, new_y))

        if spawn_positions:
            # 分裂モンスターを作成
            spawn_x, spawn_y = random.choice(spawn_positions)

            # 元のモンスターの属性をコピーして分裂体を作成
            from pyrogue.entities.actors.monster import Monster as MonsterClass

            split_monster = MonsterClass(
                char=monster.char,
                x=spawn_x,
                y=spawn_y,
                name=f"{monster.name} (split)",
                level=monster.level,
                hp=monster.hp // 2,  # HPは半分
                max_hp=monster.max_hp // 2,
                attack=monster.attack,
                defense=monster.defense,
                exp_value=monster.exp_value // 2,  # 経験値も半分
                view_range=monster.view_range,
                color=monster.color,
                ai_pattern=monster.ai_pattern,
            )

            # 親子関係を設定
            split_monster.parent_monster = monster
            monster.split_children.append(split_monster)

            # 元のモンスターのHPも半分に
            monster.hp = monster.hp // 2
            monster.max_hp = monster.max_hp // 2

            # スポナーに追加
            floor_data.monster_spawner.monsters.append(split_monster)
            floor_data.monster_spawner.occupied_positions.add((spawn_x, spawn_y))

            context.add_message(f"{monster.name} splits into two!")
            game_logger.debug(f"{monster.name} split into two monsters")

    def _can_monster_move_to(self, x: int, y: int, context: GameContext) -> bool:
        """
        モンスターが指定座標に移動可能かチェック。

        Args:
        ----
            x: 目標X座標
            y: 目標Y座標
            context: ゲームコンテキスト

        Returns:
        -------
            移動可能な場合True

        """
        floor_data = context.get_current_floor_data()
        if not floor_data:
            return False

        # 境界チェック
        if x < 0 or y < 0 or y >= floor_data.tiles.shape[0] or x >= floor_data.tiles.shape[1]:
            return False

        # タイルチェック
        tile = floor_data.tiles[y, x]
        if not getattr(tile, "walkable", False):
            return False

        # プレイヤーの位置チェック
        player = context.player
        if player.x == x and player.y == y:
            return False

        # 他のモンスターとの重複チェック
        if hasattr(floor_data, "monster_spawner"):
            for other_monster in floor_data.monster_spawner.monsters:
                if other_monster.x == x and other_monster.y == y:
                    return False

        return True

    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """
        2点間の距離を計算。

        Args:
        ----
            x1, y1: 点1の座標
            x2, y2: 点2の座標

        Returns:
        -------
            ユークリッド距離

        """
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
