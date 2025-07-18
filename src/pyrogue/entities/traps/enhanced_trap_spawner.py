"""
強化トラップ生成システム。

既存のトラップシステムを拡張し、
階層難易度管理システムと統合してより戦略的な
トラップ配置を実現します。
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np

from pyrogue.core.managers.floor_difficulty_manager import FloorDifficultyManager
from pyrogue.map.dungeon import Room
from pyrogue.utils import game_logger

from .trap import PitTrap, PoisonNeedleTrap, TeleportTrap, Trap, TrapManager


class EnhancedTrapSpawner:
    """
    強化トラップ生成クラス。

    階層難易度管理システムと統合し、
    戦略的なトラップ配置とバランス調整を行います。
    """

    def __init__(self, floor: int) -> None:
        """
        強化トラップ生成器を初期化。

        Args:
        ----
            floor: 対象となる階層

        """
        self.floor = floor
        self.trap_manager = TrapManager()

        # 階層難易度管理システムを初期化
        self.difficulty_manager = FloorDifficultyManager(floor)
        self.trap_adjustments = self.difficulty_manager.get_trap_spawn_adjustments()

        # 統計情報
        self.spawn_statistics: dict[str, Any] = {
            "total_spawned": 0,
            "by_type": {},
            "hidden_traps": 0,
            "magical_traps": 0,
            "strategic_placements": 0,
        }

        # トラップタイプの定義
        self.trap_types = {
            "pit": {"class": PitTrap, "weight": 40, "tier": 1},
            "poison": {"class": PoisonNeedleTrap, "weight": 30, "tier": 2},
            "teleport": {"class": TeleportTrap, "weight": 20, "tier": 3},
            "spike": {"class": SpikeTrap, "weight": 25, "tier": 2},
            "confusion": {"class": ConfusionTrap, "weight": 15, "tier": 3},
            "sleep": {"class": SleepTrap, "weight": 20, "tier": 2},
            "drain": {"class": DrainTrap, "weight": 10, "tier": 4},
            "explosive": {"class": ExplosiveTrap, "weight": 15, "tier": 4},
        }

        game_logger.debug(f"EnhancedTrapSpawner initialized for floor {floor}")

    def spawn_traps(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> None:
        """
        強化されたトラップ配置システム。

        Args:
        ----
            dungeon_tiles: ダンジョンのタイル配列
            rooms: ダンジョンの部屋リスト

        """
        self.trap_manager.clear_all_traps()
        self._reset_statistics()

        # 調整されたトラップ数を取得
        base_count = self.trap_adjustments["base_count"]
        count_modifier = self.trap_adjustments["count_modifier"]
        total_traps = int(base_count * count_modifier)

        if total_traps <= 0:
            return

        # 戦略的トラップの配置
        self._spawn_strategic_traps(dungeon_tiles, rooms, total_traps)

        # 通常トラップの配置
        remaining_traps = total_traps - self.spawn_statistics["strategic_placements"]
        if remaining_traps > 0:
            self._spawn_regular_traps(dungeon_tiles, rooms, remaining_traps)

        # 統計情報の更新
        self._update_statistics()

        game_logger.info(
            f"Enhanced trap spawning completed: {self.trap_manager.get_trap_count()} traps on floor {self.floor}"
        )

    def _spawn_strategic_traps(self, dungeon_tiles: np.ndarray, rooms: list[Room], total_traps: int) -> None:
        """戦略的トラップの配置。"""
        strategic_count = min(total_traps // 3, 3)  # 最大3個の戦略的トラップ

        for _ in range(strategic_count):
            strategy = self._select_trap_strategy()
            position = self._find_strategic_position(dungeon_tiles, rooms, strategy)

            if position:
                x, y = position
                trap_type = self._select_strategic_trap_type(strategy)
                trap = self._create_enhanced_trap(trap_type, x, y)

                if trap:
                    self.trap_manager.add_trap(trap)
                    self.spawn_statistics["strategic_placements"] += 1
                    self._update_trap_statistics(trap, trap_type)

    def _spawn_regular_traps(self, dungeon_tiles: np.ndarray, rooms: list[Room], count: int) -> None:
        """通常トラップの配置。"""
        for _ in range(count):
            position = self._find_optimal_position(dungeon_tiles, rooms)
            if not position:
                continue

            x, y = position
            trap_type = self._select_trap_type()
            trap = self._create_enhanced_trap(trap_type, x, y)

            if trap:
                self.trap_manager.add_trap(trap)
                self._update_trap_statistics(trap, trap_type)

    def _select_trap_strategy(self) -> str:
        """トラップ配置戦略を選択。"""
        strategies = ["guardian", "ambush", "chokepoint", "treasure_guard", "corridor"]
        difficulty_tier = self.difficulty_manager.difficulty_tier

        # 難易度に応じた戦略の重み付け
        if difficulty_tier <= 2:
            return random.choice(["guardian", "corridor"])
        if difficulty_tier <= 3:
            return random.choice(["guardian", "ambush", "corridor"])
        return random.choice(strategies)

    def _select_strategic_trap_type(self, strategy: str) -> str:
        """戦略に応じたトラップタイプを選択。"""
        strategy_types = {
            "guardian": ["pit", "spike", "poison"],
            "ambush": ["teleport", "confusion", "sleep"],
            "chokepoint": ["explosive", "drain", "pit"],
            "treasure_guard": ["poison", "drain", "explosive"],
            "corridor": ["pit", "spike", "teleport"],
        }

        available_types = strategy_types.get(strategy, ["pit", "poison"])
        available_types = [t for t in available_types if self._is_trap_type_available(t)]

        return random.choice(available_types) if available_types else "pit"

    def _select_trap_type(self) -> str:
        """通常のトラップタイプを選択。"""
        difficulty_tier = self.difficulty_manager.difficulty_tier

        # 難易度に応じた利用可能なトラップタイプ
        available_types = []
        for trap_type, info in self.trap_types.items():
            if info["tier"] <= difficulty_tier:
                available_types.append(trap_type)

        if not available_types:
            return "pit"  # フォールバック

        # 重み付き抽選
        weights = [self.trap_types[t]["weight"] for t in available_types]
        return random.choices(available_types, weights=weights, k=1)[0]

    def _is_trap_type_available(self, trap_type: str) -> bool:
        """トラップタイプが利用可能かチェック。"""
        if trap_type not in self.trap_types:
            return False

        return self.trap_types[trap_type]["tier"] <= self.difficulty_manager.difficulty_tier

    def _create_enhanced_trap(self, trap_type: str, x: int, y: int) -> Trap | None:
        """強化されたトラップを作成。"""
        if trap_type not in self.trap_types:
            return None

        trap_class = self.trap_types[trap_type]["class"]

        # 基本トラップの作成
        if trap_type == "pit":
            damage = self._calculate_enhanced_damage(10)
            trap = trap_class(x, y, damage)
        elif trap_type == "poison":
            duration = self._calculate_enhanced_duration(8)
            trap = trap_class(x, y, duration)
        elif trap_type == "teleport":
            trap = trap_class(x, y)
        elif trap_type == "spike":
            damage = self._calculate_enhanced_damage(15)
            trap = trap_class(x, y, damage)
        elif trap_type == "confusion":
            duration = self._calculate_enhanced_duration(6)
            trap = trap_class(x, y, duration)
        elif trap_type == "sleep":
            duration = self._calculate_enhanced_duration(4)
            trap = trap_class(x, y, duration)
        elif trap_type == "drain":
            drain_amount = self._calculate_enhanced_drain(5)
            trap = trap_class(x, y, drain_amount)
        elif trap_type == "explosive":
            damage = self._calculate_enhanced_damage(20)
            radius = 2
            trap = trap_class(x, y, damage, radius)
        else:
            return None

        # 隠蔽状態の決定
        if random.random() < self.trap_adjustments["hidden_trap_chance"]:
            trap.is_hidden = True
            self.spawn_statistics["hidden_traps"] += 1
        else:
            trap.is_hidden = False

        # 魔法トラップの判定
        if random.random() < self.trap_adjustments["magical_trap_chance"]:
            self._apply_magical_properties(trap)
            self.spawn_statistics["magical_traps"] += 1

        return trap

    def _calculate_enhanced_damage(self, base_damage: int) -> int:
        """強化されたダメージを計算。"""
        damage_modifier = self.trap_adjustments["trap_damage_modifier"]
        enhanced_damage = int(base_damage * damage_modifier)

        # ランダムな変動
        variance = random.randint(-20, 20)  # ±20%の変動
        final_damage = max(1, enhanced_damage + (enhanced_damage * variance // 100))

        return final_damage

    def _calculate_enhanced_duration(self, base_duration: int) -> int:
        """強化された継続時間を計算。"""
        difficulty_tier = self.difficulty_manager.difficulty_tier
        enhanced_duration = base_duration + (difficulty_tier - 1) * 2

        return max(1, enhanced_duration)

    def _calculate_enhanced_drain(self, base_drain: int) -> int:
        """強化されたドレイン量を計算。"""
        difficulty_tier = self.difficulty_manager.difficulty_tier
        enhanced_drain = base_drain + (difficulty_tier - 1)

        return max(1, enhanced_drain)

    def _apply_magical_properties(self, trap: Trap) -> None:
        """魔法的特性を適用。"""
        # 魔法トラップの特殊効果
        magical_effects = ["regenerating", "phase_shifting", "illusory", "cursed"]
        effect = random.choice(magical_effects)

        # トラップに魔法的特性を追加
        trap.magical_effect = effect

        # 見た目の変更
        if effect == "regenerating":
            trap.color = (255, 255, 0)  # 金色
        elif effect == "phase_shifting":
            trap.color = (128, 0, 128)  # 紫色
        elif effect == "illusory":
            trap.color = (0, 255, 255)  # シアン色
        elif effect == "cursed":
            trap.color = (64, 0, 0)  # 暗赤色

    def _find_strategic_position(
        self, dungeon_tiles: np.ndarray, rooms: list[Room], strategy: str
    ) -> tuple[int, int] | None:
        """戦略的位置を検索。"""
        if strategy == "guardian":
            # 部屋の入り口付近
            return self._find_room_entrance_position(dungeon_tiles, rooms)
        if strategy == "ambush":
            # 部屋の角や隠れた位置
            return self._find_ambush_position(dungeon_tiles, rooms)
        if strategy == "chokepoint":
            # 廊下の狭い場所
            return self._find_chokepoint_position(dungeon_tiles, rooms)
        if strategy == "treasure_guard":
            # 部屋の中央付近
            return self._find_treasure_guard_position(dungeon_tiles, rooms)
        if strategy == "corridor":
            # 廊下の途中
            return self._find_corridor_position(dungeon_tiles, rooms)
        return self._find_optimal_position(dungeon_tiles, rooms)

    def _find_room_entrance_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """部屋入り口付近の位置を検索。"""
        if not rooms:
            return None

        room = random.choice(rooms)
        entrance_candidates = []

        # 部屋の境界付近をチェック
        for x in range(room.x, room.x + room.width):
            for y in range(room.y, room.y + room.height):
                if self._is_near_entrance(dungeon_tiles, x, y, room):
                    entrance_candidates.append((x, y))

        return random.choice(entrance_candidates) if entrance_candidates else None

    def _find_ambush_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """待ち伏せ位置を検索。"""
        if not rooms:
            return None

        room = random.choice(rooms)

        # 部屋の角を優先
        corners = [
            (room.x + 1, room.y + 1),
            (room.x + room.width - 2, room.y + 1),
            (room.x + 1, room.y + room.height - 2),
            (room.x + room.width - 2, room.y + room.height - 2),
        ]

        for x, y in corners:
            if self._is_valid_trap_position(dungeon_tiles, x, y):
                return (x, y)

        return None

    def _find_chokepoint_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """狭い通路の位置を検索。"""
        height, width = dungeon_tiles.shape

        # 廊下の狭い部分を探す
        for _ in range(50):  # 最大50回試行
            x = random.randint(2, width - 3)
            y = random.randint(2, height - 3)

            if self._is_chokepoint(dungeon_tiles, x, y):
                return (x, y)

        return None

    def _find_treasure_guard_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """宝物守護位置を検索。"""
        if not rooms:
            return None

        # 大きな部屋の中央付近
        large_rooms = [room for room in rooms if room.width * room.height > 20]
        if large_rooms:
            room = random.choice(large_rooms)
            center_x = room.x + room.width // 2
            center_y = room.y + room.height // 2

            if self._is_valid_trap_position(dungeon_tiles, center_x, center_y):
                return (center_x, center_y)

        return None

    def _find_corridor_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """廊下の位置を検索。"""
        height, width = dungeon_tiles.shape

        # 廊下を探す
        for _ in range(100):  # 最大100回試行
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)

            if self._is_corridor(dungeon_tiles, x, y):
                return (x, y)

        return None

    def _find_optimal_position(self, dungeon_tiles: np.ndarray, rooms: list[Room]) -> tuple[int, int] | None:
        """最適な配置位置を検索。"""
        height, width = dungeon_tiles.shape

        # 歩行可能なタイルから選択
        for _ in range(50):  # 最大50回試行
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)

            if self._is_valid_trap_position(dungeon_tiles, x, y):
                return (x, y)

        return None

    def _is_valid_trap_position(self, dungeon_tiles: np.ndarray, x: int, y: int) -> bool:
        """トラップ配置位置の有効性チェック。"""
        if not (0 <= x < dungeon_tiles.shape[1] and 0 <= y < dungeon_tiles.shape[0]):
            return False

        # 歩行可能で、既存のトラップがない位置
        return dungeon_tiles[y, x].walkable and self.trap_manager.get_trap_at(x, y) is None

    def _is_near_entrance(self, dungeon_tiles: np.ndarray, x: int, y: int, room: Room) -> bool:
        """部屋の入り口付近かチェック。"""
        # 部屋の境界から1タイル以内
        return (
            room.x <= x <= room.x + room.width - 1
            and room.y <= y <= room.y + room.height - 1
            and (x == room.x + 1 or x == room.x + room.width - 2 or y == room.y + 1 or y == room.y + room.height - 2)
        )

    def _is_chokepoint(self, dungeon_tiles: np.ndarray, x: int, y: int) -> bool:
        """狭い通路かチェック。"""
        if not dungeon_tiles[y, x].walkable:
            return False

        # 周囲の歩行可能なタイルが少ない場合は狭い通路
        walkable_neighbors = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < dungeon_tiles.shape[1]
                    and 0 <= ny < dungeon_tiles.shape[0]
                    and dungeon_tiles[ny, nx].walkable
                ):
                    walkable_neighbors += 1

        return walkable_neighbors <= 3  # 3個以下なら狭い通路

    def _is_corridor(self, dungeon_tiles: np.ndarray, x: int, y: int) -> bool:
        """廊下かチェック。"""
        if not dungeon_tiles[y, x].walkable:
            return False

        # 部屋の中でない歩行可能なタイルは廊下
        return True  # 簡易実装

    def _reset_statistics(self) -> None:
        """統計情報のリセット。"""
        self.spawn_statistics = {
            "total_spawned": 0,
            "by_type": {},
            "hidden_traps": 0,
            "magical_traps": 0,
            "strategic_placements": 0,
        }

    def _update_trap_statistics(self, trap: Trap, trap_type: str) -> None:
        """トラップ統計の更新。"""
        self.spawn_statistics["total_spawned"] += 1

        if trap_type not in self.spawn_statistics["by_type"]:
            self.spawn_statistics["by_type"][trap_type] = 0
        self.spawn_statistics["by_type"][trap_type] += 1

    def _update_statistics(self) -> None:
        """統計情報の最終更新。"""
        game_logger.debug(f"Trap spawn statistics for floor {self.floor}: {self.spawn_statistics}")

    def get_trap_manager(self) -> TrapManager:
        """トラップマネージャーを取得。"""
        return self.trap_manager

    def get_spawn_statistics(self) -> dict[str, Any]:
        """生成統計情報を取得。"""
        return {
            "floor": self.floor,
            "difficulty_tier": self.difficulty_manager.difficulty_tier,
            "spawn_statistics": self.spawn_statistics,
            "adjustments_applied": self.trap_adjustments,
        }


# 新しいトラップクラスの定義
class SpikeTrap(Trap):
    """スパイクトラップ。"""

    def __init__(self, x: int, y: int, damage: int = 15) -> None:
        super().__init__(x, y)
        self.name = "Spike Trap"
        self.trap_type = "spike"
        self.damage = damage
        self.char = "^"
        self.color = (192, 192, 192)  # 銀色

    def activate(self, context) -> None:
        player = context.player
        actual_damage = max(1, self.damage - player.get_defense())
        player.hp = max(0, player.hp - actual_damage)

        context.add_message(f"Sharp spikes pierce you! You take {actual_damage} damage!")
        self.reveal()


class ConfusionTrap(Trap):
    """混乱トラップ。"""

    def __init__(self, x: int, y: int, duration: int = 6) -> None:
        super().__init__(x, y)
        self.name = "Confusion Trap"
        self.trap_type = "confusion"
        self.duration = duration
        self.char = "^"
        self.color = (255, 255, 0)  # 黄色

    def activate(self, context) -> None:
        from pyrogue.entities.actors.status_effects import ConfusionEffect

        player = context.player
        confusion_effect = ConfusionEffect(duration=self.duration)
        player.status_effects.add_effect(confusion_effect)

        context.add_message("You step on a strange sigil and feel disoriented!")
        self.reveal()


class SleepTrap(Trap):
    """睡眠トラップ。"""

    def __init__(self, x: int, y: int, duration: int = 4) -> None:
        super().__init__(x, y)
        self.name = "Sleep Trap"
        self.trap_type = "sleep"
        self.duration = duration
        self.char = "^"
        self.color = (100, 100, 200)  # 青色

    def activate(self, context) -> None:
        # 睡眠エフェクトの実装が必要
        context.add_message("You feel drowsy and fall asleep!")
        self.reveal()


class DrainTrap(Trap):
    """ドレイントラップ。"""

    def __init__(self, x: int, y: int, drain_amount: int = 5) -> None:
        super().__init__(x, y)
        self.name = "Drain Trap"
        self.trap_type = "drain"
        self.drain_amount = drain_amount
        self.char = "^"
        self.color = (64, 0, 64)  # 暗紫色

    def activate(self, context) -> None:
        # 経験値やステータスをドレイン
        context.add_message("You feel your life force being drained!")
        self.reveal()


class ExplosiveTrap(Trap):
    """爆発トラップ。"""

    def __init__(self, x: int, y: int, damage: int = 20, radius: int = 2) -> None:
        super().__init__(x, y)
        self.name = "Explosive Trap"
        self.trap_type = "explosive"
        self.damage = damage
        self.radius = radius
        self.char = "^"
        self.color = (255, 128, 0)  # オレンジ色

    def activate(self, context) -> None:
        player = context.player
        actual_damage = max(1, self.damage - player.get_defense())
        player.hp = max(0, player.hp - actual_damage)

        context.add_message(f"BOOM! The trap explodes! You take {actual_damage} damage!")
        self.reveal()
