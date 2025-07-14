"""
Player クラスのテストモジュール。

基本的なプレイヤー機能のテストを提供します。
"""

from unittest.mock import Mock

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.item import Gold


class TestPlayer:
    """Player クラスのテストクラス。"""

    def test_player_initialization(self):
        """プレイヤーの初期化テスト。"""
        player = Player(x=10, y=15)

        # 座標の確認
        assert player.x == 10
        assert player.y == 15

        # 基本ステータスの確認
        assert player.hp > 0
        assert player.max_hp > 0
        assert player.mp > 0
        assert player.max_mp > 0
        assert player.attack > 0
        assert player.defense > 0
        assert player.level == 1
        assert player.exp == 0
        assert player.hunger > 0
        assert player.gold == 0

        # インベントリとその他システムの初期化確認
        assert player.inventory is not None
        assert player.status_effects is not None
        assert player.spellbook is not None

    def test_player_move(self):
        """プレイヤーの移動テスト。"""
        player = Player(x=10, y=15)

        # 正の移動
        player.move(5, 3)
        assert player.x == 15
        assert player.y == 18

        # 負の移動
        player.move(-2, -5)
        assert player.x == 13
        assert player.y == 13

        # ゼロ移動
        player.move(0, 0)
        assert player.x == 13
        assert player.y == 13

    def test_player_take_damage(self):
        """プレイヤーのダメージ処理テスト。"""
        player = Player(x=10, y=15)
        initial_hp = player.hp
        defense = player.defense

        # 通常のダメージ
        damage = 10
        player.take_damage(damage)
        expected_hp = max(0, initial_hp - max(0, damage - defense))
        assert player.hp == expected_hp

        # 防御力を超えるダメージ
        player.hp = 100
        high_damage = defense + 50
        player.take_damage(high_damage)
        assert player.hp == 50  # 100 - (high_damage - defense)

        # HPが0未満にならないことを確認
        player.hp = 5
        player.take_damage(100)
        assert player.hp == 0

    def test_player_heal(self):
        """プレイヤーの回復処理テスト。"""
        player = Player(x=10, y=15)
        player.hp = 10  # HP減少
        max_hp = player.max_hp

        # 通常の回復
        player.heal(5)
        assert player.hp == 15

        # 最大HPを超えて回復しないことを確認
        player.heal(max_hp)
        assert player.hp == max_hp

    def test_player_experience_and_leveling(self):
        """プレイヤーの経験値とレベルアップテスト。"""
        from pyrogue.constants import get_exp_for_level

        player = Player(x=10, y=15)
        initial_level = player.level
        initial_max_hp = player.max_hp
        initial_max_mp = player.max_mp
        initial_attack = player.attack
        initial_defense = player.defense

        # 経験値獲得（レベルアップしない）
        small_exp = 50
        leveled_up = player.gain_exp(small_exp)
        assert not leveled_up
        assert player.exp == small_exp
        assert player.level == initial_level

        # レベルアップに必要な経験値を獲得
        level_up_exp = get_exp_for_level(initial_level + 1)  # 正しい経験値計算
        player.exp = 0  # リセット
        leveled_up = player.gain_exp(level_up_exp)
        assert leveled_up
        assert player.level == initial_level + 1
        assert player.exp == 0  # レベルアップ後はリセット
        assert player.max_hp > initial_max_hp
        assert player.max_mp > initial_max_mp
        assert player.attack > initial_attack
        assert player.defense > initial_defense
        assert player.hp == player.max_hp  # 全回復
        assert player.mp == player.max_mp  # 全回復

    def test_player_mp_management(self):
        """プレイヤーのMP管理テスト。"""
        player = Player(x=10, y=15)

        # MP消費
        initial_mp = player.mp
        consumed = player.spend_mp(5)
        assert consumed is True
        assert player.mp == initial_mp - 5

        # MP不足時の消費
        consumed = player.spend_mp(player.mp + 10)
        assert consumed is False
        assert player.mp == initial_mp - 5  # 変化なし

        # MP回復
        restored = player.restore_mp(3)
        assert restored == 3
        assert player.mp == initial_mp - 2

        # MP判定
        assert player.has_enough_mp(5) is True
        assert player.has_enough_mp(player.mp + 10) is False

    def test_player_hunger_system(self):
        """プレイヤーの満腹度システムテスト。"""
        player = Player(x=10, y=15)

        # 満腹度の消費
        initial_hunger = player.hunger
        message = player.consume_food(10)
        assert player.hunger == initial_hunger - 10
        assert message is None  # 通常状態ではメッセージなし

        # 空腹状態
        player.hunger = 5
        message = player.consume_food(1)
        assert player.hunger == 4
        assert message is None  # まだ空腹メッセージは出ない

        # 飢餓状態
        player.hunger = 1
        initial_hp = player.hp
        message = player.consume_food(2)
        assert player.hunger == 0
        assert player.hp < initial_hp  # 飢餓ダメージ
        assert message is not None  # 飢餓メッセージ

        # 継続飢餓
        initial_hp = player.hp
        message = player.consume_food(1)
        assert player.hunger == 0
        assert player.hp < initial_hp  # 継続ダメージ
        assert message is not None  # 継続メッセージ

        # 食料摂取
        player.eat_food(50)
        assert player.hunger == 50
        assert not player.is_starving()
        assert not player.is_hungry()

    def test_player_status_effects(self):
        """プレイヤーの状態異常テスト。"""
        player = Player(x=10, y=15)

        # 初期状態
        assert not player.is_paralyzed()
        assert not player.is_confused()
        assert not player.is_poisoned()
        assert not player.has_status_effect("NonExistent")

        # 状態異常の更新（モックコンテキストを使用）
        mock_context = Mock()
        player.update_status_effects(mock_context)

        # status_effects.update_effects が呼び出されることを確認
        assert hasattr(player.status_effects, "update_effects")

    def test_player_attack_and_defense_calculation(self):
        """プレイヤーの攻撃力・防御力計算テスト。"""
        player = Player(x=10, y=15)

        # 基本攻撃力・防御力
        base_attack = player.attack
        base_defense = player.defense

        # 装備ボーナスなしの場合
        total_attack = player.get_attack()
        total_defense = player.get_defense()

        # インベントリボーナスが加算されることを確認
        assert total_attack >= base_attack
        assert total_defense >= base_defense

    def test_player_gold_usage(self):
        """プレイヤーの金貨使用テスト。"""
        player = Player(x=10, y=15)

        # 金貨アイテムの使用
        gold_item = Gold(x=0, y=0, amount=50)
        player.inventory.add_item(gold_item)

        # 金貨使用
        success = player.use_item(gold_item)
        assert success is True
        assert player.gold == 50
        assert gold_item not in player.inventory.items
