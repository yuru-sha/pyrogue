"""
プレイヤーモジュール。

このモジュールは、プレイヤーキャラクターの定義と関連機能を提供します。
プレイヤーのステータス管理、アイテムの使用、装備の管理、
レベルアップシステムなどを統合的に処理します。

Example:
    >>> player = Player(x=10, y=10)
    >>> player.take_damage(5)
    >>> player.gain_exp(50)

"""

from dataclasses import dataclass

from pyrogue.config import CONFIG
from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.actors.player_status import PlayerStatusFormatter
from pyrogue.entities.actors.status_effects import StatusEffectManager
from pyrogue.entities.magic.spells import Spellbook
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


@dataclass
class Player:
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

    Attributes:
        x: プレイヤーのX座標
        y: プレイヤーのY座標
        hp: 現在のHP
        max_hp: 最大HP
        attack: 基本攻撃力
        defense: 基本防御力
        level: 現在のレベル
        exp: 経験値
        hunger: 満腹度（0-100）
        gold: 所持金貨
        inventory: インベントリインスタンス

    """

    x: int = 0
    y: int = 0
    hp: int = CONFIG.player.INITIAL_HP
    max_hp: int = CONFIG.player.INITIAL_HP
    mp: int = 10  # 初期MP
    max_mp: int = 10  # 最大MP
    attack: int = CONFIG.player.INITIAL_ATTACK
    defense: int = CONFIG.player.INITIAL_DEFENSE
    level: int = 1
    exp: int = 0
    hunger: int = CONFIG.player.MAX_HUNGER
    gold: int = 0
    light_duration: int = 0  # Light効果の残りターン数
    base_light_radius: int = 10  # 基本視野範囲
    light_radius: int = 10  # 現在の視野範囲

    def __init__(self, x: int, y: int) -> None:
        """
        プレイヤーを初期化。

        指定された位置にプレイヤーを配置し、インベントリを初期化します。
        ゲーム開始時の初期状態でステータスを設定します。

        Args:
            x: 初期位置のX座標
            y: 初期位置のY座標

        """
        self.x = x
        self.y = y
        self.inventory = Inventory()
        self.gold = 0
        self.status_effects = StatusEffectManager()
        self.spellbook = Spellbook()

    def move(self, dx: int, dy: int) -> None:
        """
        指定した方向にプレイヤーを移動。

        Args:
            dx: X軸方向の移動量
            dy: Y軸方向の移動量

        """
        self.x += dx
        self.y += dy

    def take_damage(self, amount: int) -> None:
        """
        ダメージを受けるHPを減少。

        防御力を考慮した実ダメージを計算し、HPから差し引きます。
        HPは0未満にはなりません。

        Args:
            amount: 受けるダメージ量

        """
        self.hp = max(0, self.hp - max(0, amount - self.defense))

    def heal(self, amount: int) -> None:
        """
        HPを回復。

        指定された量だけHPを回復します。最大HPを超えて回復することはありません。

        Args:
            amount: 回復するHP量

        """
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_exp(self, amount: int) -> bool:
        """
        経験値を獲得し、レベルアップをチェック。

        経験値を加算し、レベルアップ条件を満たした場合は自動的に
        レベルアップ処理を実行します。現在のレベル×100が必要経験値です。

        Args:
            amount: 獲得する経験値

        Returns:
            レベルアップした場合はTrue、そうでなければFalse

        """
        self.exp += amount
        if self.exp >= self.level * CONFIG.player.EXPERIENCE_MULTIPLIER:
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """
        レベルアップ時の処理。

        レベル、最大HP、最大MP、攻撃力、防御力を上昇させ、
        HPとMPを全回復し、経験値をリセットします。
        """
        self.level += 1
        self.max_hp += CONFIG.player.LEVEL_UP_HP_BONUS
        self.hp = self.max_hp
        # MPを5ずつ増加（レベルアップ時）
        self.max_mp += 5
        self.mp = self.max_mp
        self.attack += CONFIG.player.LEVEL_UP_ATTACK_BONUS
        self.defense += CONFIG.player.LEVEL_UP_DEFENSE_BONUS
        self.exp = 0

    def consume_food(self, amount: int = 1) -> str | None:
        """
        食料を消費して満腹度を減少し、MPの自然回復を行う。

        時間経過やアクションによる満腹度の減少を表現します。
        満腹度は0未満にはなりません。

        Args:
            amount: 消費する満腹度

        Returns:
            飢餓メッセージ。飢餓状態でない場合はNone

        """
        old_hunger = self.hunger
        self.hunger = max(0, self.hunger - amount)

        # MPの自然回復（満腹状態でない場合）
        if self.hunger > 0 and self.mp < self.max_mp:
            # 10%の確率でMP+1回復
            import random
            if random.random() < 0.1:
                self.mp = min(self.max_mp, self.mp + 1)

        # 飢餓状態をチェック
        if self.hunger <= 0:
            # 飢餓状態: 防御力を無視した直接ダメージ
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
            context: 効果適用のためのコンテキスト

        """
        self.status_effects.update_effects(context)

    def has_status_effect(self, name: str) -> bool:
        """
        指定された状態異常があるかどうかを判定。

        Args:
            name: 判定する状態異常の名前

        Returns:
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

    def spend_mp(self, amount: int) -> bool:
        """
        MPを消費する。

        Args:
            amount: 消費するMP量

        Returns:
            消費に成功した場合はTrue、MPが不足している場合はFalse

        """
        if self.mp >= amount:
            self.mp -= amount
            return True
        return False

    def restore_mp(self, amount: int) -> int:
        """
        MPを回復する。

        Args:
            amount: 回復するMP量

        Returns:
            実際に回復したMP量

        """
        old_mp = self.mp
        self.mp = min(self.max_mp, self.mp + amount)
        return self.mp - old_mp

    def has_enough_mp(self, amount: int) -> bool:
        """
        指定されたMP量があるかどうかを判定。

        Args:
            amount: 必要なMP量

        Returns:
            MP量が十分な場合はTrue、不足している場合はFalse

        """
        return self.mp >= amount

    def is_starving(self) -> bool:
        """飢餓状態かどうかを判定。"""
        return self.hunger <= 0

    def is_hungry(self) -> bool:
        """空腹状態かどうかを判定。"""
        return self.hunger < CONFIG.player.MAX_HUNGER * 0.1

    def eat_food(self, amount: int = 25) -> None:
        """
        食料を食べて満腹度を回復。

        指定された量だけ満腹度を回復します。満腹度の最大値は100です。

        Args:
            amount: 回復する満腹度

        """
        self.hunger = min(CONFIG.player.MAX_HUNGER, self.hunger + amount)

    def get_attack(self) -> int:
        """
        現在の攻撃力を計算。

        基本攻撃力に装備アイテムのボーナスを加算した
        実際の攻撃力を返します。

        Returns:
            装備ボーナスを含む総攻撃力

        """
        base_attack = self.attack
        bonus = self.inventory.get_attack_bonus()
        return base_attack + bonus

    def get_defense(self) -> int:
        """
        現在の防御力を計算。

        基本防御力に装備アイテムのボーナスを加算した
        実際の防御力を返します。

        Returns:
            装備ボーナスを含む総防御力

        """
        base_defense = self.defense
        bonus = self.inventory.get_defense_bonus()
        return base_defense + bonus

    def equip_item(self, item: Item) -> Item | None:
        """
        アイテムを装備。

        武器、防具、指輪のみ装備可能です。既に同じスロットに
        装備がある場合は自動的に外してインベントリに戻します。

        Args:
            item: 装備するアイテム

        Returns:
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
            slot: 装備スロット名（"weapon", "armor", "ring_left", "ring_right"）

        Returns:
            外したアイテム。ない場合はNone

        """
        item = self.inventory.unequip(slot)
        if item:
            self.inventory.add_item(item)
        return item

    def use_item(self, item: Item, context=None) -> bool:
        """
        アイテムを使用して効果を適用。

        アイテムの種類に応じて適切な効果を適用し、
        成功した場合はインベントリからアイテムを除去します。

        Args:
            item: 使用するアイテム
            context: 効果適用のためのコンテキスト（ゲーム画面など）

        Returns:
            使用に成功した場合はTrue、失敗した場合はFalse

        """
        if isinstance(item, (Scroll, Potion, Food)):
            if context is None:
                return False
            # 新しいeffectシステムを使用
            success = item.apply_effect(context)
            if success:
                self.inventory.remove_item(item)
            return success

        if isinstance(item, Gold):
            # 金貨を所持金に加算
            self.gold += item.amount
            self.inventory.remove_item(item)
            return True

        return False

    def get_status_text(self) -> str:
        """
        ステータス表示用のテキストを取得。

        プレイヤーの総合ステータスと装備状態を表示用の
        文字列としてフォーマットして返します。

        Returns:
            プレイヤーのステータスと装備情報を含む文字列

        """
        return PlayerStatusFormatter.format_status(self)

    def get_stats_dict(self) -> dict:
        """
        ステータス辞書を取得。

        ゲームオーバー画面や勝利画面で使用する
        ステータス情報を辞書形式で返します。

        Returns:
            プレイヤーのステータス情報を含む辞書

        """
        return PlayerStatusFormatter.format_stats_dict(self)
