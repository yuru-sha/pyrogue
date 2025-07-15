"""
プレイヤーモジュール。

このモジュールは、プレイヤーキャラクターの定義と関連機能を提供します。
プレイヤーのステータス管理、アイテムの使用、装備の管理、
レベルアップシステムなどを統合的に処理します。

Example:
-------
    >>> player = Player(x=10, y=10)
    >>> player.take_damage(5)
    >>> player.gain_exp(50)

"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext

from pyrogue.config import CONFIG
from pyrogue.constants import HungerConstants
from pyrogue.entities.actors.actor import Actor
from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.actors.player_status import PlayerStatusFormatter
from pyrogue.entities.actors.status_effects import StatusEffectManager
from pyrogue.entities.items.amulet import AmuletOfYendor
from pyrogue.entities.items.identification import ItemIdentification
from pyrogue.entities.items.item import (
    Armor,
    Food,
    Gold,
    Item,
    Potion,
    Ring,
    Scroll,
    Weapon,
)


class Player(Actor):
    """
    プレイヤーキャラクターを表すクラス。

    プレイヤーの位置、ステータス、インベントリ、装備等を管理し、
    戦闘、アイテム使用、レベルアップ等の機能を提供します。

    特徴:
        - 動的なステータス計算（装備ボーナス等）
        - インベントリと装備システムの統合
        - 経験値ベースのレベルアップシステム
        - 満腹度システムとサバイバル要素
        - アイテムの使用と効果適用

    Attributes
    ----------
        exp: 経験値
        hunger: 満腹度（0-100）
        gold: 所持金貨
        inventory: インベントリインスタンス

    """

    def __init__(self, x: int, y: int) -> None:
        """
        プレイヤーを初期化。

        指定された位置にプレイヤーを配置し、インベントリを初期化します。
        ゲーム開始時の初期状態でステータスを設定します。

        Args:
        ----
            x: 初期位置のX座標
            y: 初期位置のY座標

        """
        # 基底クラスの属性を初期化
        super().__init__(
            x=x,
            y=y,
            name="Player",
            hp=CONFIG.player.INITIAL_HP,
            max_hp=CONFIG.player.INITIAL_HP,
            attack=CONFIG.player.INITIAL_ATTACK,
            defense=CONFIG.player.INITIAL_DEFENSE,
            level=1,
            is_hostile=False,
        )

        # Player固有の属性を初期化
        self.exp = 0
        self.hunger = CONFIG.player.MAX_HUNGER
        self.gold = 0
        self.light_duration = 0
        self.base_light_radius = 10
        self.light_radius = 10

        # スコア統計情報
        self.monsters_killed = 0
        self.deepest_floor = 1
        self.turns_played = 0
        self.items_used = 0

        # ゲーム目標フラグ
        self.has_amulet = False

        # システムの初期化
        self.inventory = Inventory()
        self.status_effects = StatusEffectManager()
        self.identification = ItemIdentification()

    # move, heal は基底クラスから継承
    # take_damageはウィザードモード対応のためオーバーライド

    def take_damage(self, amount: int, context: GameContext | None = None) -> None:
        """
        ダメージを受けてHPを減少（ウィザードモード対応）。

        ウィザードモード時はダメージを無効化し、警告メッセージを表示します。
        通常時は基底クラスの処理を実行します。

        Args:
        ----
            amount: 受けるダメージ量
            context: ゲームコンテキスト（ウィザードモード判定用）

        """
        # ウィザードモードチェック
        if context and hasattr(context, "game_logic") and context.game_logic.is_wizard_mode():
            # ウィザードモード時はダメージを無効化
            if hasattr(context, "add_message"):
                context.add_message(f"[Wizard] Damage {amount} blocked!")
            return

        # 通常時は基底クラスの処理を実行
        super().take_damage(amount)

    def gain_exp(self, amount: int) -> bool:
        """
        経験値を獲得し、レベルアップをチェック。

        経験値を加算し、レベルアップ条件を満たした場合は自動的に
        レベルアップ処理を実行します。必要経験値は指数関数的に増加します。

        Args:
        ----
            amount: 獲得する経験値

        Returns:
        -------
            レベルアップした場合はTrue、そうでなければFalse

        """
        from pyrogue.constants import get_exp_for_level

        self.exp += amount
        required_exp = get_exp_for_level(self.level + 1)
        if self.exp >= required_exp:
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """
        レベルアップ時の処理。

        レベル、最大HP、攻撃力、防御力を上昇させ、
        HPを全回復し、経験値をリセットします。
        """
        self.level += 1
        self.max_hp += CONFIG.player.LEVEL_UP_HP_BONUS
        self.hp = self.max_hp
        self.attack += CONFIG.player.LEVEL_UP_ATTACK_BONUS
        self.defense += CONFIG.player.LEVEL_UP_DEFENSE_BONUS
        self.exp = 0

    def consume_food(self, amount: int = 1, context: GameContext | None = None) -> str | None:
        """
        食料を消費して満腹度を減少する。

        時間経過やアクションによる満腹度の減少を表現します。
        満腹度は0未満にはなりません。

        Args:
        ----
            amount: 消費する満腹度

        Returns:
        -------
            飢餓メッセージ。飢餓状態でない場合はNone

        """
        old_hunger = self.hunger
        self.hunger = max(0, self.hunger - amount)

        # 飢餓状態をチェック
        if self.hunger <= 0:
            # 飢餓状態: 防御力を無視した直接ダメージ
            if context:
                self.take_damage(1, context)
            else:
                # contextがない場合は直接HPを減らす（後方互換性）
                self.hp = max(0, self.hp - 1)

            if old_hunger > 0:
                # 初めて飢餓状態になった場合
                return "You are starving! You feel weak from hunger."
            # 継続して飢餓状態
            return "You are still starving and losing health!"
        if self.hunger < 10:  # 空腹状態
            if old_hunger >= 10:
                return "You are getting hungry."

        return None

    def update_light_effect(self) -> None:
        """Light効果のターン経過処理"""
        if self.light_duration > 0:
            self.light_duration -= 1
            if self.light_duration <= 0:
                # 効果終了：視野範囲を基本値に戻す
                self.light_radius = self.base_light_radius

    def apply_light_effect(self, duration: int = 50, radius: int = 15) -> None:
        """Light効果を適用"""
        self.light_duration = duration
        self.light_radius = radius

    def update_status_effects(self, context) -> None:
        """
        状態異常のターン経過処理。

        すべての状態異常の効果を適用し、継続ターン数を更新します。
        効果が切れた状態異常は自動的に削除されます。

        Args:
        ----
            context: 効果適用のためのコンテキスト

        """
        self.status_effects.update_effects(context)

    def has_status_effect(self, name: str) -> bool:
        """
        指定された状態異常があるかどうかを判定。

        Args:
        ----
            name: 判定する状態異常の名前

        Returns:
        -------
            状態異常が存在する場合はTrue、そうでなければFalse

        """
        return self.status_effects.has_effect(name)

    def is_paralyzed(self) -> bool:
        """麻痺状態かどうかを判定。"""
        return self.has_status_effect("Paralysis")

    def is_confused(self) -> bool:
        """混乱状態かどうかを判定。"""
        return self.has_status_effect("Confusion")

    def is_poisoned(self) -> bool:
        """毒状態かどうかを判定。"""
        return self.has_status_effect("Poison")

    def is_starving(self) -> bool:
        """飢餓状態かどうかを判定。"""
        return self.hunger <= 0

    def is_hungry(self) -> bool:
        """空腹状態かどうかを判定。"""
        return self.hunger < HungerConstants.HUNGRY_THRESHOLD

    def get_hunger_level(self) -> str:
        """現在の飢餓レベルを取得。"""
        if self.hunger >= HungerConstants.FULL_THRESHOLD:
            return "Full"
        if self.hunger >= HungerConstants.CONTENT_THRESHOLD:
            return "Content"
        if self.hunger >= HungerConstants.HUNGRY_THRESHOLD:
            return "Hungry"
        if self.hunger >= HungerConstants.VERY_HUNGRY_THRESHOLD:
            return "Very Hungry"
        if self.hunger >= HungerConstants.STARVING_THRESHOLD:
            return "Starving"
        return "Dying"

    def get_hunger_attack_penalty(self) -> int:
        """飢餓による攻撃力ペナルティを取得。"""
        if self.hunger >= HungerConstants.HUNGRY_THRESHOLD:
            return 0
        if self.hunger >= HungerConstants.VERY_HUNGRY_THRESHOLD:
            return HungerConstants.HUNGRY_ATTACK_PENALTY
        if self.hunger >= HungerConstants.STARVING_THRESHOLD:
            return HungerConstants.VERY_HUNGRY_ATTACK_PENALTY
        return HungerConstants.STARVING_ATTACK_PENALTY

    def get_hunger_defense_penalty(self) -> int:
        """飢餓による防御力ペナルティを取得。"""
        if self.hunger >= HungerConstants.HUNGRY_THRESHOLD:
            return 0
        if self.hunger >= HungerConstants.VERY_HUNGRY_THRESHOLD:
            return HungerConstants.HUNGRY_DEFENSE_PENALTY
        if self.hunger >= HungerConstants.STARVING_THRESHOLD:
            return HungerConstants.VERY_HUNGRY_DEFENSE_PENALTY
        return HungerConstants.STARVING_DEFENSE_PENALTY

    def eat_food(self, amount: int = 25) -> None:
        """
        食料を食べて満腹度を回復。

        指定された量だけ満腹度を回復します。満腹度の最大値は100です。

        Args:
        ----
            amount: 回復する満腹度

        """
        self.hunger = min(CONFIG.player.MAX_HUNGER, self.hunger + amount)

    def get_attack(self) -> int:
        """
        現在の攻撃力を計算。

        基本攻撃力に装備アイテムのボーナスを加算し、
        飢餓ペナルティを適用した実際の攻撃力を返します。

        Returns
        -------
            装備ボーナスと飢餓ペナルティを含む総攻撃力

        """
        base_attack = self.attack
        equipment_bonus = self.inventory.get_attack_bonus()
        hunger_penalty = self.get_hunger_attack_penalty()
        total_attack = base_attack + equipment_bonus - hunger_penalty
        return max(1, total_attack)  # 最低1の攻撃力は保証

    def get_defense(self) -> int:
        """
        現在の防御力を計算。

        基本防御力に装備アイテムのボーナスを加算し、
        飢餓ペナルティを適用した実際の防御力を返します。

        Returns
        -------
            装備ボーナスと飢餓ペナルティを含む総防御力

        """
        base_defense = self.defense
        equipment_bonus = self.inventory.get_defense_bonus()
        hunger_penalty = self.get_hunger_defense_penalty()
        total_defense = base_defense + equipment_bonus - hunger_penalty
        return max(0, total_defense)  # 0未満にはならない

    def equip_item(self, item: Item) -> Item | None:
        """
        アイテムを装備。

        武器、防具、指輪のみ装備可能です。既に同じスロットに
        装備がある場合は自動的に外してインベントリに戻します。

        Args:
        ----
            item: 装備するアイテム

        Returns:
        -------
            外したアイテム。ない場合はNone

        """
        if isinstance(item, (Weapon, Armor, Ring)):
            old_item = self.inventory.equip(item)
            self.inventory.remove_item(item)
            if old_item:
                self.inventory.add_item(old_item)
            return old_item
        return None

    def unequip_item(self, slot: str) -> Item | None:
        """
        指定したスロットの装備を外す。

        外したアイテムは自動的にインベントリに追加されます。

        Args:
        ----
            slot: 装備スロット名（"weapon", "armor", "ring_left", "ring_right"）

        Returns:
        -------
            外したアイテム。ない場合はNone

        """
        item = self.inventory.unequip(slot)
        if item:
            self.inventory.add_item(item)
        return item

    def use_item(self, item: Item, context: GameContext | None = None) -> bool:
        """
        アイテムを使用して効果を適用。

        アイテムの種類に応じて適切な効果を適用し、
        成功した場合はインベントリからアイテムを除去します。

        Args:
        ----
            item: 使用するアイテム
            context: 効果適用のためのコンテキスト（ゲーム画面など）

        Returns:
        -------
            使用に成功した場合はTrue、失敗した場合はFalse

        """
        if isinstance(item, (Scroll, Potion, Food)):
            if context is None:
                return False
            # 新しいeffectシステムを使用
            success = item.apply_effect(context)
            if success:
                self.inventory.remove_item(item)
                self.record_item_use()
            return success

        if isinstance(item, Gold):
            # 金貨を所持金に加算
            self.gold += item.amount
            self.inventory.remove_item(item)
            return True

        if isinstance(item, AmuletOfYendor):
            # Amulet of Yendorの効果を適用
            success = item.apply_effect(context)
            if success:
                self.inventory.remove_item(item)
                self.record_item_use()
            return success

        return False

    def get_status_text(self) -> str:
        """
        ステータス表示用のテキストを取得。

        プレイヤーの総合ステータスと装備状態を表示用の
        文字列としてフォーマットして返します。

        Returns
        -------
            プレイヤーのステータスと装備情報を含む文字列

        """
        return PlayerStatusFormatter.format_status(self)

    def get_stats_dict(self) -> dict:
        """
        ステータス辞書を取得。

        ゲームオーバー画面や勝利画面で使用する
        ステータス情報を辞書形式で返します。

        Returns
        -------
            プレイヤーのステータス情報を含む辞書

        """
        return PlayerStatusFormatter.format_stats_dict(self)

    def record_monster_kill(self) -> None:
        """モンスター撃破を記録"""
        self.monsters_killed += 1

    def update_deepest_floor(self, floor: int) -> None:
        """到達最深階層を更新"""
        self.deepest_floor = max(self.deepest_floor, floor)

    def increment_turn(self) -> None:
        """ターン数を増加"""
        self.turns_played += 1

    def record_item_use(self) -> None:
        """アイテム使用を記録"""
        self.items_used += 1

    def calculate_score(self) -> int:
        """
        スコアを計算

        Returns
        -------
            総合スコア

        """
        # オリジナルRogue風スコア計算
        score = 0
        score += self.gold * 10  # 金貨 x10
        score += self.exp * 5  # 経験値 x5
        score += self.level * 100  # レベル x100
        score += self.monsters_killed * 50  # モンスター撃破 x50
        score += self.deepest_floor * 200  # 到達階層 x200
        return score
