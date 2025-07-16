"""
強化された飢餓システムのテストモジュール。

このモジュールは、新しく実装された段階的な飢餓システム、
ペナルティシステム、ボーナス効果、ダメージシステムを検証し、
オリジナルRogue風の飢餓体験が正しく実装されていることを確認します。
"""

from unittest.mock import Mock

from pyrogue.constants import HungerConstants
from pyrogue.core.managers.game_context import GameContext
from pyrogue.core.managers.turn_manager import TurnManager
from pyrogue.entities.actors.player import Player


class TestEnhancedHungerSystem:
    """強化された飢餓システムのテスト。"""

    def setup_method(self):
        """各テストメソッドの前に呼ばれるセットアップ。"""
        self.player = Player(x=10, y=10)
        self.player.hunger = HungerConstants.MAX_HUNGER
        self.context = Mock(spec=GameContext)
        self.context.player = self.player
        self.context.add_message = Mock()
        self.context.get_current_floor_number = Mock(return_value=5)

        # game_logicの適切なモック設定
        self.context.game_logic = Mock()
        self.context.game_logic.is_wizard_mode = Mock(return_value=False)

        self.turn_manager = TurnManager()

    def test_hunger_level_classification(self):
        """飢餓レベルの分類テスト。"""
        # 満腹状態
        self.player.hunger = 90
        assert self.player.get_hunger_level() == "Full"

        # 満足状態
        self.player.hunger = 70
        assert self.player.get_hunger_level() == "Content"

        # 空腹状態（正しい値に修正）
        self.player.hunger = 35  # 30以上、60未満なので"Hungry"
        assert self.player.get_hunger_level() == "Hungry"

        # 非常に空腹状態（25は30未満、15以上）
        self.player.hunger = 25  # 30未満、15以上なので"Very Hungry"
        assert self.player.get_hunger_level() == "Very Hungry"

        # 飢餓状態（5以上でStarving）
        self.player.hunger = 5
        assert self.player.get_hunger_level() == "Starving"

        # 瀕死状態（5未満でDying）
        self.player.hunger = 3
        assert self.player.get_hunger_level() == "Dying"

    def test_hunger_attack_penalties(self):
        """飢餓による攻撃力ペナルティテスト。"""
        base_attack = self.player.attack

        # 通常状態（ペナルティなし）
        self.player.hunger = 50
        assert self.player.get_hunger_attack_penalty() == 0
        assert self.player.get_attack() >= base_attack

        # 空腹状態（軽微なペナルティ）
        self.player.hunger = 25
        assert self.player.get_hunger_attack_penalty() == HungerConstants.HUNGRY_ATTACK_PENALTY

        # 非常に空腹状態（中程度のペナルティ）
        self.player.hunger = 10
        assert self.player.get_hunger_attack_penalty() == HungerConstants.VERY_HUNGRY_ATTACK_PENALTY

        # 飢餓状態（重大なペナルティ）
        self.player.hunger = 3
        assert self.player.get_hunger_attack_penalty() == HungerConstants.STARVING_ATTACK_PENALTY

        # 攻撃力は最低1を保証
        expected_attack = base_attack - HungerConstants.STARVING_ATTACK_PENALTY
        assert self.player.get_attack() == max(1, expected_attack)

    def test_hunger_defense_penalties(self):
        """飢餓による防御力ペナルティテスト。"""
        base_defense = self.player.defense

        # 通常状態（ペナルティなし）
        self.player.hunger = 50
        assert self.player.get_hunger_defense_penalty() == 0

        # 空腹状態（軽微なペナルティ）
        self.player.hunger = 25
        assert self.player.get_hunger_defense_penalty() == HungerConstants.HUNGRY_DEFENSE_PENALTY

        # 非常に空腹状態（中程度のペナルティ）
        self.player.hunger = 10
        assert self.player.get_hunger_defense_penalty() == HungerConstants.VERY_HUNGRY_DEFENSE_PENALTY

        # 飢餓状態（重大なペナルティ）
        self.player.hunger = 3
        assert self.player.get_hunger_defense_penalty() == HungerConstants.STARVING_DEFENSE_PENALTY

        # 防御力は0未満にならない
        expected_defense = base_defense - HungerConstants.STARVING_DEFENSE_PENALTY
        assert self.player.get_defense() == max(0, expected_defense)

    def test_hunger_decrease_over_time(self):
        """時間経過による飢餓の進行テスト。"""
        initial_hunger = HungerConstants.MAX_HUNGER
        self.player.hunger = initial_hunger

        # 飢餓減少間隔未満では変化なし
        for i in range(1, HungerConstants.HUNGER_DECREASE_INTERVAL):
            self.turn_manager.turn_count = i
            self.turn_manager._process_hunger_system(self.context)
            assert self.player.hunger == initial_hunger

        # 減少間隔に達すると飢餓が減少
        self.turn_manager.turn_count = HungerConstants.HUNGER_DECREASE_INTERVAL
        self.turn_manager._process_hunger_system(self.context)
        assert self.player.hunger == initial_hunger - HungerConstants.HUNGER_DECREASE_RATE

    def test_hunger_state_change_messages(self):
        """飢餓状態変化時のメッセージテスト。"""
        # 満腹から満足状態への変化
        self.player.hunger = HungerConstants.FULL_THRESHOLD
        self.turn_manager.turn_count = HungerConstants.HUNGER_DECREASE_INTERVAL
        self.turn_manager._process_hunger_system(self.context)

        self.context.add_message.assert_called()
        calls = [call.args[0] for call in self.context.add_message.call_args_list]
        assert any("no longer full" in msg for msg in calls)

    def test_full_bonus_effects(self):
        """満腹時のボーナス効果テスト。"""
        # HPを部分的に減らして満腹状態に
        self.player.hunger = HungerConstants.FULL_THRESHOLD + 10
        self.player.hp = self.player.max_hp - 5

        # randomをモックして確実にHP回復が発動するようにする
        import random
        from unittest.mock import patch

        with patch.object(random, "random", return_value=0.01):  # 5%確率より低い値でHP回復を確実に発動
            old_hp = self.player.hp

            self.turn_manager._apply_full_bonus_effects(self.context, self.player)

            # HP回復効果が発動したことを確認
            assert self.player.hp > old_hp
            assert self.player.hp == old_hp + 1

            # メッセージが追加されたことを確認
            self.context.add_message.assert_called_with("You feel refreshed!")

        # HP満タンの場合は効果が発動しないことを確認
        self.player.hp = self.player.max_hp

        with patch.object(random, "random", return_value=0.01):
            old_hp = self.player.hp

            self.turn_manager._apply_full_bonus_effects(self.context, self.player)

            # HP満タンなので回復しない
            assert self.player.hp == old_hp

    def test_starvation_damage(self):
        """飢餓状態でのダメージテスト。"""
        self.player.hunger = HungerConstants.STARVING_THRESHOLD - 1
        initial_hp = self.player.hp

        # ダメージ間隔に達するまではダメージなし
        for i in range(1, HungerConstants.STARVING_DAMAGE_INTERVAL):
            self.turn_manager.turn_count = i
            self.turn_manager._process_hunger_damage(self.context, self.player)
            assert self.player.hp == initial_hp

        # ダメージ間隔に達するとダメージ
        self.turn_manager.turn_count = HungerConstants.STARVING_DAMAGE_INTERVAL
        self.turn_manager._process_hunger_damage(self.context, self.player)
        assert self.player.hp == initial_hp - HungerConstants.STARVING_DAMAGE

    def test_very_hungry_damage(self):
        """非常に空腹状態でのダメージテスト。"""
        self.player.hunger = HungerConstants.VERY_HUNGRY_THRESHOLD - 1
        initial_hp = self.player.hp

        # ダメージ間隔に達するとダメージ
        self.turn_manager.turn_count = HungerConstants.VERY_HUNGRY_DAMAGE_INTERVAL
        self.turn_manager._process_hunger_damage(self.context, self.player)
        assert self.player.hp == initial_hp - 1

    def test_starvation_death(self):
        """飢餓死のテスト。"""
        self.player.hunger = 0
        self.player.hp = 1  # 1HPで飢餓状態

        # ゲームオーバー処理のモック（ウィザードモード設定を保持）
        self.context.game_logic.record_game_over = Mock()
        self.context.engine = Mock()
        self.context.engine.game_over = Mock()

        # 飢餓ダメージで死亡
        self.turn_manager.turn_count = HungerConstants.STARVING_DAMAGE_INTERVAL
        self.turn_manager._process_hunger_damage(self.context, self.player)

        assert self.player.hp == 0
        self.context.game_logic.record_game_over.assert_called_with("Starvation")
        self.context.engine.game_over.assert_called()

    def test_hunger_recovery_from_food(self):
        """食料による飢餓回復テスト。"""
        self.player.hunger = 20
        recovery_amount = 30

        self.player.eat_food(recovery_amount)
        assert self.player.hunger == 50

        # 最大値を超えない
        self.player.eat_food(60)
        assert self.player.hunger == HungerConstants.MAX_HUNGER

    def test_hunger_system_integration(self):
        """飢餓システム全体の統合テスト。"""
        # 満腹状態から開始
        self.player.hunger = HungerConstants.MAX_HUNGER
        self.player.hp = self.player.max_hp - 2

        # 複数ターン進行させて状態変化を確認
        messages_received = []

        def capture_message(msg):
            messages_received.append(msg)

        self.context.add_message.side_effect = capture_message

        # 100ターン分実行
        for turn in range(1, 101):
            self.turn_manager.turn_count = turn
            self.turn_manager._process_hunger_system(self.context)

        # 飢餓が進行していることを確認
        assert self.player.hunger < HungerConstants.MAX_HUNGER

        # 何らかの状態変化メッセージが送信されていることを確認
        assert len(messages_received) > 0

        # 攻撃力・防御力にペナルティが適用されていることを確認
        if self.player.hunger < HungerConstants.HUNGRY_THRESHOLD:
            assert self.player.get_hunger_attack_penalty() > 0
            assert self.player.get_hunger_defense_penalty() > 0

    def test_hunger_thresholds_consistency(self):
        """飢餓閾値の一貫性テスト。"""
        # 閾値が正しい順序になっていることを確認
        assert HungerConstants.MAX_HUNGER > HungerConstants.FULL_THRESHOLD
        assert HungerConstants.FULL_THRESHOLD > HungerConstants.CONTENT_THRESHOLD
        assert HungerConstants.CONTENT_THRESHOLD > HungerConstants.HUNGRY_THRESHOLD
        assert HungerConstants.HUNGRY_THRESHOLD > HungerConstants.VERY_HUNGRY_THRESHOLD
        assert HungerConstants.VERY_HUNGRY_THRESHOLD > HungerConstants.STARVING_THRESHOLD
        assert HungerConstants.STARVING_THRESHOLD >= 0

    def test_hunger_penalties_escalation(self):
        """飢餓ペナルティの段階的エスカレーションテスト。"""
        # ペナルティが段階的に厳しくなることを確認
        assert HungerConstants.HUNGRY_ATTACK_PENALTY < HungerConstants.VERY_HUNGRY_ATTACK_PENALTY
        assert HungerConstants.VERY_HUNGRY_ATTACK_PENALTY < HungerConstants.STARVING_ATTACK_PENALTY

        assert HungerConstants.HUNGRY_DEFENSE_PENALTY < HungerConstants.VERY_HUNGRY_DEFENSE_PENALTY
        assert HungerConstants.VERY_HUNGRY_DEFENSE_PENALTY < HungerConstants.STARVING_DEFENSE_PENALTY
