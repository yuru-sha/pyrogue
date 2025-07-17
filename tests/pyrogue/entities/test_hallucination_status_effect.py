"""
幻覚状態異常システムのテストモジュール。

このモジュールは、幻覚状態異常の基本機能、
視覚混乱システム、ポーション効果、モンスター攻撃による発症を検証します。
"""

from unittest.mock import Mock, patch

import pytest

from pyrogue.core.managers.combat_manager import CombatManager
from pyrogue.core.managers.game_context import GameContext
from pyrogue.entities.actors.monster import Monster
from pyrogue.entities.actors.player import Player
from pyrogue.entities.actors.status_effects import (
    HallucinationEffect,
    StatusEffectManager,
)
from pyrogue.entities.items.effects import EffectContext, HallucinationPotionEffect


class TestHallucinationStatusEffect:
    """幻覚状態異常の基本機能テスト。"""

    def setup_method(self):
        """各テストメソッドの前に呼ばれるセットアップ。"""
        self.player = Player(x=10, y=10)
        self.hallucination = HallucinationEffect(duration=8)
        self.status_manager = StatusEffectManager()

    def test_hallucination_effect_initialization(self):
        """幻覚効果の初期化テスト。"""
        assert self.hallucination.name == "Hallucination"
        assert self.hallucination.description == "幻覚状態：視覚混乱"
        assert self.hallucination.duration == 8
        assert self.hallucination.original_duration == 8

    def test_hallucination_effect_activation(self):
        """幻覚効果の有効性テスト。"""
        assert self.hallucination.is_active()

        # ターン数を0にすると無効になる
        self.hallucination.duration = 0
        assert not self.hallucination.is_active()

    def test_hallucination_display_name(self):
        """幻覚効果の表示名テスト。"""
        assert self.hallucination.get_display_name() == "Hallucination(8)"

        self.hallucination.duration = 3
        assert self.hallucination.get_display_name() == "Hallucination(3)"

    def test_hallucination_apply_per_turn(self):
        """ターンごとの幻覚効果適用テスト。"""
        # モックコンテキストを作成
        context = Mock()
        context.add_message = Mock()

        # 効果を適用
        result = self.hallucination.apply_per_turn(context)

        # 継続中のはずでTrue
        assert result is True
        assert self.hallucination.duration == 7

        # メッセージが呼ばれた
        context.add_message.assert_called_once()

    def test_hallucination_duration_update(self):
        """幻覚効果の継続時間更新テスト。"""
        # 初期8ターン
        assert self.hallucination.duration == 8

        # 7回更新
        for i in range(7):
            result = self.hallucination.update_duration()
            assert result is True
            assert self.hallucination.duration == 7 - i

        # 最後の1回で終了
        result = self.hallucination.update_duration()
        assert result is False
        assert self.hallucination.duration == 0


class TestHallucinationStatusManager:
    """幻覚状態異常の管理システムテスト。"""

    def setup_method(self):
        """セットアップ。"""
        self.player = Player(x=10, y=10)
        self.manager = StatusEffectManager()
        self.hallucination = HallucinationEffect(duration=6)

    def test_add_hallucination_effect(self):
        """幻覚効果の追加テスト。"""
        self.manager.add_effect(self.hallucination)

        assert self.manager.has_effect("Hallucination")
        assert len(self.manager.get_active_effects()) == 1

    def test_hallucination_effect_overlap(self):
        """幻覚効果の重複テスト。"""
        # 短い幻覚を追加
        short_hallucination = HallucinationEffect(duration=3)
        self.manager.add_effect(short_hallucination)
        assert self.manager.effects["Hallucination"].duration == 3

        # より長い幻覚を追加（これが優先される）
        long_hallucination = HallucinationEffect(duration=10)
        self.manager.add_effect(long_hallucination)
        assert self.manager.effects["Hallucination"].duration == 10

    def test_hallucination_effect_removal(self):
        """幻覚効果の削除テスト。"""
        self.manager.add_effect(self.hallucination)
        assert self.manager.has_effect("Hallucination")

        success = self.manager.remove_effect("Hallucination")
        assert success is True
        assert not self.manager.has_effect("Hallucination")

        # 存在しない効果の削除
        success = self.manager.remove_effect("NonExistent")
        assert success is False

    def test_hallucination_effect_summary(self):
        """幻覚効果の要約テスト。"""
        self.manager.add_effect(self.hallucination)
        summary = self.manager.get_effect_summary()
        assert "Hallucination(6)" in summary


class TestHallucinationPotion:
    """幻覚ポーション効果のテスト。"""

    def setup_method(self):
        """セットアップ。"""
        self.player = Player(x=10, y=10)
        self.potion_effect = HallucinationPotionEffect(duration=8)
        self.context = Mock(spec=EffectContext)
        self.context.player = self.player

    def test_hallucination_potion_initialization(self):
        """幻覚ポーションの初期化テスト。"""
        assert self.potion_effect.name == "Hallucination"
        assert "hallucinations for 8 turns" in self.potion_effect.description

    def test_hallucination_potion_application(self):
        """幻覚ポーション効果の適用テスト。"""
        # ポーション効果を適用
        result = self.potion_effect.apply(self.context)

        # 正常に適用された
        assert result is True

        # プレイヤーに幻覚効果が追加された
        assert self.player.status_effects.has_effect("Hallucination")

        # 継続時間が正しい
        effect = self.player.status_effects.effects["Hallucination"]
        assert effect.duration == 8

    def test_hallucination_potion_can_apply(self):
        """幻覚ポーション適用可能性テスト。"""
        assert self.potion_effect.can_apply(self.context) is True


class TestMonsterHallucinationAttack:
    """モンスター攻撃による幻覚発症のテスト。"""

    def setup_method(self):
        """セットアップ。"""
        self.player = Player(x=10, y=10)
        self.context = Mock(spec=GameContext)
        self.context.player = self.player
        self.context.add_message = Mock()
        self.combat_manager = CombatManager()

    def test_psychic_monster_hallucination_attack(self):
        """精神攻撃モンスターの幻覚攻撃テスト。"""
        # 精神攻撃モンスターを作成
        psychic_monster = Monster(
            char="@",
            x=11,
            y=10,
            name="Dream Eater",
            level=7,
            hp=15,
            max_hp=15,
            attack=9,
            defense=3,
            exp_value=12,
            view_range=6,
            color=(255, 20, 147),
            ai_pattern="psychic",
        )

        # 確実に幻覚効果が発動するようにモック
        with patch("random.random", return_value=0.1):  # 30%より低い値
            self.combat_manager._handle_special_attack_effects(psychic_monster, self.context)

        # 幻覚状態異常が追加されたかチェック
        assert self.player.status_effects.has_effect("Hallucination")

        # メッセージが表示されたかチェック
        self.context.add_message.assert_called()

    def test_hallucinogenic_monster_attack(self):
        """幻覚性モンスターの攻撃テスト。"""
        # 幻覚性モンスターを作成
        hallucinogenic_monster = Monster(
            char="f",
            x=11,
            y=10,
            name="Phantom Fungus",
            level=5,
            hp=10,
            max_hp=10,
            attack=6,
            defense=2,
            exp_value=8,
            view_range=4,
            color=(138, 43, 226),
            ai_pattern="hallucinogenic",
        )

        # 確実に幻覚効果が発動するようにモック
        with patch("random.random", return_value=0.1):  # 30%より低い値
            self.combat_manager._handle_special_attack_effects(hallucinogenic_monster, self.context)

        # 幻覚状態異常が追加されたかチェック
        assert self.player.status_effects.has_effect("Hallucination")

    def test_normal_monster_no_hallucination(self):
        """通常モンスターは幻覚を引き起こさないテスト。"""
        # 通常モンスターを作成
        normal_monster = Monster(
            char="O",
            x=11,
            y=10,
            name="Orc",
            level=5,
            hp=12,
            max_hp=12,
            attack=10,
            defense=3,
            exp_value=8,
            view_range=5,
            color=(0, 200, 0),
            ai_pattern="basic",
        )

        self.combat_manager._handle_special_attack_effects(normal_monster, self.context)

        # 幻覚状態異常は追加されない
        assert not self.player.status_effects.has_effect("Hallucination")

    def test_hallucination_attack_probability(self):
        """幻覚攻撃の確率テスト。"""
        psychic_monster = Monster(
            char="@",
            x=11,
            y=10,
            name="Dream Eater",
            level=7,
            hp=15,
            max_hp=15,
            attack=9,
            defense=3,
            exp_value=12,
            view_range=6,
            color=(255, 20, 147),
            ai_pattern="psychic",
        )

        # 確率が高すぎて発動しない場合
        with patch("random.random", return_value=0.8):  # 30%より高い値
            self.combat_manager._handle_special_attack_effects(psychic_monster, self.context)

        # 幻覚状態異常は追加されない
        assert not self.player.status_effects.has_effect("Hallucination")


class TestVisualConfusionSystem:
    """視覚混乱システムのテスト。"""

    def test_player_has_hallucination_detection(self):
        """プレイヤーの幻覚状態検出テスト。"""
        player = Player(x=10, y=10)

        # 最初は幻覚状態ではない
        assert not player.status_effects.has_effect("Hallucination")

        # 幻覚効果を追加
        hallucination = HallucinationEffect(duration=5)
        player.status_effects.add_effect(hallucination)

        # 幻覚状態を検出
        assert player.status_effects.has_effect("Hallucination")

    @patch("pyrogue.ui.components.game_renderer.random.choice")
    @patch("pyrogue.ui.components.game_renderer.random.randint")
    def test_hallucination_character_randomization(self, mock_randint, mock_choice):
        """幻覚時の文字ランダム化テスト。"""
        from pyrogue.ui.components.game_renderer import GameRenderer

        # モックゲームスクリーンを作成
        game_screen = Mock()
        renderer = GameRenderer(game_screen)

        # ランダム値をモック
        mock_choice.return_value = "X"
        mock_randint.side_effect = [200, 100, 50]  # RGB値

        # 幻覚文字を取得
        char = renderer._get_hallucination_char()
        color = renderer._get_hallucination_color()

        assert char == "X"
        assert color == (200, 100, 50)

        # ランダム関数が呼ばれた
        mock_choice.assert_called_once()
        assert mock_randint.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])
