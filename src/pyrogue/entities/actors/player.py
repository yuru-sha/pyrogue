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

from pyrogue.entities.actors.inventory import Inventory
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
    hp: int = 20
    max_hp: int = 20
    attack: int = 5
    defense: int = 3
    level: int = 1
    exp: int = 0
    hunger: int = 100  # 満腹度（100が最大）
    gold: int = 0

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
        if self.exp >= self.level * 100:  # 簡単な経験値テーブル（レベル×100）
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
        self.max_hp += 5
        self.hp = self.max_hp
        self.attack += 2
        self.defense += 1
        self.exp = 0  # 経験値をリセットして次のレベルへ

    def consume_food(self, amount: int = 1) -> None:
        """
        食料を消費して満腹度を減少。

        時間経過やアクションによる満腹度の減少を表現します。
        満腹度は0未満にはなりません。

        Args:
            amount: 消費する満腹度

        """
        self.hunger = max(0, self.hunger - amount)

    def eat_food(self, amount: int = 25) -> None:
        """
        食料を食べて満腹度を回復。

        指定された量だけ満腹度を回復します。満腹度の最大値は100です。

        Args:
            amount: 回復する満腹度

        """
        self.hunger = min(100, self.hunger + amount)

    def get_attack(self) -> int:
        """
        現在の攻撃力を計算。

        基本攻撃力に装備アイテムのボーナスを加算した
        実際の攻撃力を返します。

        Returns:
            装備ボーナスを含む総攻撃力

        """
        base_attack = 5  # プレイヤーの基本攻撃力
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
        base_defense = 2  # プレイヤーの基本防御力
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

    def use_item(self, item: Item) -> bool:
        """
        アイテムを使用して効果を適用。

        アイテムの種類に応じて適切な効果を適用し、
        成功した場合はインベントリからアイテムを除去します。

        Args:
            item: 使用するアイテム

        Returns:
            使用に成功した場合はTrue、失敗した場合はFalse

        """
        if isinstance(item, Scroll):
            # 巻物の効果をプレイヤーに適用
            success = item.apply_effect(self)
            if success:
                self.inventory.remove_item(item)
            return success

        if isinstance(item, Potion):
            # ポーションの効果をプレイヤーに適用
            success = item.apply_effect(self)
            if success:
                self.inventory.remove_item(item)
            return success

        if isinstance(item, Food):
            # 食料を食べて満腹度を回復
            self.hunger = min(100, self.hunger + item.nutrition)
            self.inventory.remove_item(item)
            return True

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
        weapon = self.inventory.get_equipped_item_name("weapon")
        armor = self.inventory.get_equipped_item_name("armor")
        ring_l = self.inventory.get_equipped_item_name("ring_left")
        ring_r = self.inventory.get_equipped_item_name("ring_right")

        return (
            f"Lv:{self.level} HP:{self.hp}/{self.max_hp} "
            f"Atk:{self.get_attack()} Def:{self.get_defense()} "
            f"Hunger:{self.hunger}% Exp:{self.exp} Gold:{self.gold}\n"
            f"Weap:{weapon} Armor:{armor} Ring(L):{ring_l} Ring(R):{ring_r}"
        )
