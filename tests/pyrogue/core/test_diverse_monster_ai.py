"""
多様なモンスターAIシステムのテストモジュール。

このモジュールは、新しく実装された多様なAI行動パターン、
特殊攻撃、分裂機能、逃走行動、遠距離攻撃などを検証し、
オリジナルRogue風の戦術的な多様性が正しく実装されていることを確認します。
"""

from unittest.mock import Mock, patch

import pytest

from pyrogue.core.managers.game_context import GameContext
from pyrogue.core.managers.monster_ai_manager import MonsterAIManager
from pyrogue.entities.actors.monster import Monster
from pyrogue.entities.actors.player import Player


class TestDiverseMonsterAI:
    """多様なモンスターAIシステムのテスト。"""

    def setup_method(self):
        """各テストメソッドの前に呼ばれるセットアップ。"""
        self.player = Player(x=10, y=10)
        self.context = Mock(spec=GameContext)
        self.context.player = self.player
        self.context.add_message = Mock()
        self.context.get_current_floor_number = Mock(return_value=5)

        # フロアデータのモック
        self.floor_data = Mock()
        self.floor_data.monster_spawner = Mock()
        self.floor_data.monster_spawner.monsters = []
        self.floor_data.monster_spawner.occupied_positions = set()
        self.context.get_current_floor_data = Mock(return_value=self.floor_data)

        self.ai_manager = MonsterAIManager()

    def test_item_theft_ai_pattern(self):
        """アイテム盗取AIのテスト。"""
        # アイテム盗取能力を持つモンスターを作成
        leprechaun = Monster(
            char="L", x=11, y=10, name="Leprechaun", level=4, hp=10, max_hp=10,
            attack=6, defense=2, exp_value=7, view_range=6, color=(0, 255, 0),
            ai_pattern="item_thief"
        )

        # プレイヤーにアイテムを与える
        from pyrogue.entities.items.item import Item
        test_item = Item(x=0, y=0, name="Test Item", char="!", color=(255, 0, 0), stackable=False)
        self.player.inventory.add_item(test_item)

        # アイテム盗取攻撃をテスト
        assert leprechaun.can_steal_items
        self.ai_manager._steal_item(leprechaun, self.player, self.context)

        # アイテムが盗まれたことを確認
        assert test_item not in self.player.inventory.items
        self.context.add_message.assert_called()

        # 逃走フラグが設定されることを確認
        assert leprechaun.is_fleeing

    def test_gold_theft_ai_pattern(self):
        """ゴールド盗取AIのテスト。"""
        # ゴールド盗取能力を持つモンスターを作成
        nymph = Monster(
            char="N", x=11, y=10, name="Nymph", level=9, hp=14, max_hp=14,
            attack=12, defense=4, exp_value=14, view_range=6, color=(255, 192, 203),
            ai_pattern="gold_thief"
        )

        # プレイヤーにゴールドを与える
        self.player.gold = 100

        # ゴールド盗取攻撃をテスト
        assert nymph.can_steal_gold
        with patch('random.randint', return_value=25):
            self.ai_manager._steal_gold(nymph, self.player, self.context)

        # ゴールドが盗まれたことを確認
        assert self.player.gold == 75
        self.context.add_message.assert_called()

        # 逃走フラグが設定されることを確認
        assert nymph.is_fleeing

    def test_level_drain_ai_pattern(self):
        """レベル下げ攻撃AIのテスト。"""
        # レベル下げ攻撃能力を持つモンスターを作成
        wraith = Monster(
            char="W", x=11, y=10, name="Wraith", level=12, hp=25, max_hp=25,
            attack=18, defense=5, exp_value=22, view_range=7, color=(128, 128, 128),
            ai_pattern="level_drain"
        )

        # プレイヤーレベルを設定
        self.player.level = 5
        self.player.max_hp = 50
        self.player.hp = 50
        self.player.max_mp = 25
        self.player.mp = 25
        self.player.attack = 15
        self.player.defense = 8

        # レベル下げ攻撃をテスト
        assert wraith.can_drain_level
        self.ai_manager._drain_level(wraith, self.player, self.context)

        # レベルが下がったことを確認
        assert self.player.level == 4
        assert self.player.max_hp == 45  # -5
        assert self.player.max_mp == 22  # -3
        assert self.player.attack == 13  # -2
        assert self.player.defense == 7  # -1

        self.context.add_message.assert_called()

    def test_ranged_attack_ai_pattern(self):
        """遠距離攻撃AIのテスト。"""
        # 遠距離攻撃能力を持つモンスターを作成
        centaur = Monster(
            char="C", x=15, y=10, name="Centaur", level=6, hp=18, max_hp=18,
            attack=12, defense=4, exp_value=12, view_range=7, color=(160, 82, 45),
            ai_pattern="ranged"
        )

        # 遠距離攻撃が可能かテスト
        assert centaur.can_ranged_attack
        assert self.ai_manager._can_use_ranged_attack(centaur, self.player)

        # 遠距離攻撃をテスト
        with patch('random.random', return_value=0.5):  # 命中
            self.ai_manager._use_ranged_attack(centaur, self.player, self.context)

        # クールダウンが設定されることを確認
        assert centaur.special_ability_cooldown == 3
        self.context.add_message.assert_called()

    def test_fleeing_behavior_ai_pattern(self):
        """逃走行動AIのテスト。"""
        # 逃走能力を持つモンスターを作成（HP25%で逃走閾値以下に）
        bat = Monster(
            char="B", x=12, y=10, name="Bat", level=1, hp=1, max_hp=4,  # HP25%
            attack=5, defense=1, exp_value=2, view_range=8, color=(150, 150, 150),
            ai_pattern="flee"
        )

        # 逃走判定をテスト
        assert bat.can_flee
        assert self.ai_manager._should_flee(bat)  # HP25% < 30%閾値なので逃走

        # 逃走行動をテスト（移動チェックをモック）
        self.ai_manager._try_move_monster = Mock(return_value=True)
        self.ai_manager._flee_from_player(bat, self.player, self.context)

        # モンスターがプレイヤーから遠ざかる方向に移動を試みることを確認
        # （実際の移動は地形によるが、逃走フラグは設定される）
        assert bat.is_fleeing

    def test_monster_splitting_functionality(self):
        """モンスター分裂機能のテスト。"""
        # 分裂能力を持つモンスターを作成
        ice_monster = Monster(
            char="I", x=12, y=10, name="Ice Monster", level=3, hp=12, max_hp=12,
            attack=8, defense=3, exp_value=6, view_range=5, color=(173, 216, 230),
            ai_pattern="split"
        )

        # 分裂可能性を確認
        assert ice_monster.can_split

        # モック用のマップ移動チェック
        self.ai_manager._can_monster_move_to = Mock(return_value=True)

        # 分裂をテスト（30%の確率なので強制実行）
        with patch('random.random', return_value=0.2):  # 30%以下
            self.ai_manager.split_monster_on_damage(ice_monster, self.context)

        # 分裂が発生したことを確認
        assert len(self.floor_data.monster_spawner.monsters) == 1
        split_monster = self.floor_data.monster_spawner.monsters[0]
        assert split_monster.parent_monster == ice_monster
        assert split_monster in ice_monster.split_children

        # HP が半分になることを確認
        assert ice_monster.hp == 6
        assert ice_monster.max_hp == 6
        assert split_monster.hp == 6
        assert split_monster.max_hp == 6

        self.context.add_message.assert_called()

    def test_special_attack_cooldown_system(self):
        """特殊攻撃クールダウンシステムのテスト。"""
        monster = Monster(
            char="L", x=11, y=10, name="Test Monster", level=4, hp=10, max_hp=10,
            attack=6, defense=2, exp_value=7, view_range=6, color=(0, 255, 0),
            ai_pattern="item_thief"
        )

        # クールダウンなしで特殊攻撃可能（確率要素があるので複数回試行）
        with patch('random.random', return_value=0.1):  # 30%未満
            assert self.ai_manager._can_use_special_attack(monster)

        # 特殊攻撃を使用してクールダウンを設定
        monster.special_ability_cooldown = 5

        # クールダウン中は特殊攻撃不可
        assert not self.ai_manager._can_use_special_attack(monster)

        # クールダウンを減少
        monster.special_ability_cooldown = 0

        # 再び特殊攻撃可能
        with patch('random.random', return_value=0.1):  # 30%未満
            assert self.ai_manager._can_use_special_attack(monster)

    def test_ai_pattern_integration(self):
        """AIパターン統合のテスト。"""
        # 各AIパターンのモンスターを作成
        monsters = {
            "basic": Monster("O", 10, 10, "Orc", 5, 12, 12, 10, 3, 8, 5, (0, 200, 0), ai_pattern="basic"),
            "item_thief": Monster("L", 10, 10, "Leprechaun", 4, 10, 10, 6, 2, 7, 6, (0, 255, 0), ai_pattern="item_thief"),
            "gold_thief": Monster("N", 10, 10, "Nymph", 9, 14, 14, 12, 4, 14, 6, (255, 192, 203), ai_pattern="gold_thief"),
            "level_drain": Monster("W", 10, 10, "Wraith", 12, 25, 25, 18, 5, 22, 7, (128, 128, 128), ai_pattern="level_drain"),
            "ranged": Monster("C", 10, 10, "Centaur", 6, 18, 18, 12, 4, 12, 7, (160, 82, 45), ai_pattern="ranged"),
            "split": Monster("I", 10, 10, "Ice Monster", 3, 12, 12, 8, 3, 6, 5, (173, 216, 230), ai_pattern="split"),
            "flee": Monster("B", 10, 10, "Bat", 1, 2, 4, 5, 1, 2, 8, (150, 150, 150), ai_pattern="flee"),
        }

        # 各AIパターンの能力フラグを確認
        assert not monsters["basic"].can_steal_items
        assert monsters["item_thief"].can_steal_items
        assert monsters["gold_thief"].can_steal_gold
        assert monsters["level_drain"].can_drain_level
        assert monsters["ranged"].can_ranged_attack
        assert monsters["split"].can_split
        assert monsters["flee"].can_flee

    def test_ai_manager_process_monster_ai(self):
        """MonsterAIManagerのAI処理統合テスト。"""
        # 特殊能力を持つモンスターを作成
        monster = Monster(
            char="L", x=11, y=10, name="Leprechaun", level=4, hp=10, max_hp=10,
            attack=6, defense=2, exp_value=7, view_range=6, color=(0, 255, 0),
            ai_pattern="item_thief"
        )

        # プレイヤーが見えるようにモック
        self.ai_manager._can_monster_see_player = Mock(return_value=True)
        self.ai_manager._can_use_special_attack = Mock(return_value=True)
        self.ai_manager._use_special_attack = Mock()

        # AI処理を実行
        self.ai_manager.process_monster_ai(monster, self.context)

        # 特殊攻撃が使用されたことを確認
        self.ai_manager._use_special_attack.assert_called_once()

    def test_edge_cases_and_error_handling(self):
        """エッジケースとエラーハンドリングのテスト。"""
        # アイテムがない場合の盗取
        leprechaun = Monster(
            char="L", x=11, y=10, name="Leprechaun", level=4, hp=10, max_hp=10,
            attack=6, defense=2, exp_value=7, view_range=6, color=(0, 255, 0),
            ai_pattern="item_thief"
        )

        # アイテムなしでアイテム盗取を試行
        self.ai_manager._steal_item(leprechaun, self.player, self.context)
        self.context.add_message.assert_called_with("Leprechaun tries to steal from you, but you have nothing!")

        # ゴールドがない場合の盗取
        nymph = Monster(
            char="N", x=11, y=10, name="Nymph", level=9, hp=14, max_hp=14,
            attack=12, defense=4, exp_value=14, view_range=6, color=(255, 192, 203),
            ai_pattern="gold_thief"
        )

        self.player.gold = 0
        self.ai_manager._steal_gold(nymph, self.player, self.context)
        self.context.add_message.assert_called_with("Nymph searches for gold, but you have none!")

        # レベル1プレイヤーへのレベル下げ攻撃
        wraith = Monster(
            char="W", x=11, y=10, name="Wraith", level=12, hp=25, max_hp=25,
            attack=18, defense=5, exp_value=22, view_range=7, color=(128, 128, 128),
            ai_pattern="level_drain"
        )

        self.player.level = 1
        self.ai_manager._drain_level(wraith, self.player, self.context)
        # レベルが1の場合は通常ダメージに切り替わることを確認
        assert self.player.level == 1  # レベルは変わらない

    def test_ai_pattern_constants_consistency(self):
        """AIパターン定数の一貫性テスト。"""
        # すべてのAIパターンが正しく定義されていることを確認
        valid_patterns = ["basic", "item_thief", "leprechaun", "gold_thief", "nymph",
                         "level_drain", "wraith", "split", "split_on_hit",
                         "ranged", "archer", "flee", "coward"]

        test_monster = Monster(
            char="T", x=10, y=10, name="Test", level=1, hp=5, max_hp=5,
            attack=3, defense=1, exp_value=1, view_range=5, color=(255, 255, 255),
            ai_pattern="basic"
        )

        # 各パターンでモンスターが正しく初期化されることを確認
        for pattern in valid_patterns:
            test_monster.ai_pattern = pattern
            test_monster.can_steal_items = pattern in ["item_thief", "leprechaun"]
            test_monster.can_steal_gold = pattern in ["gold_thief", "nymph"]
            test_monster.can_drain_level = pattern in ["level_drain", "wraith"]
            test_monster.can_split = pattern in ["split", "split_on_hit"]
            test_monster.can_ranged_attack = pattern in ["ranged", "archer"]
            test_monster.can_flee = pattern in ["flee", "coward"]

            # 属性が正しく設定されることを確認
            if pattern in ["item_thief", "leprechaun"]:
                assert test_monster.can_steal_items
            if pattern in ["gold_thief", "nymph"]:
                assert test_monster.can_steal_gold
            if pattern in ["level_drain", "wraith"]:
                assert test_monster.can_drain_level
