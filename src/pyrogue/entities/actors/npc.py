"""
NPCモジュール。

このモジュールは、友好的・中立的なNPC（Non-Player Character）エンティティを定義します。
商人、情報提供者、クエストギバーなどのNPCを統合的に管理します。
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pyrogue.entities.actors.actor import Actor
from pyrogue.entities.actors.status_effects import StatusEffectManager

if TYPE_CHECKING:
    from pyrogue.entities.actors.inventory import Inventory
    from pyrogue.entities.items.item import Item


class NPCDisposition(Enum):
    """NPC の態度・性格を定義する列挙型。"""

    FRIENDLY = "friendly"  # 友好的
    NEUTRAL = "neutral"  # 中立的
    HOSTILE = "hostile"  # 敵対的（モンスター化）


class NPCType(Enum):
    """NPC の種類を定義する列挙型。"""

    MERCHANT = "merchant"  # 商人
    GUARD = "guard"  # 警備員
    VILLAGER = "villager"  # 村人
    PRIEST = "priest"  # 僧侶
    MAGE = "mage"  # 魔術師


class NPC(Actor):
    """
    NPCの基本クラス。

    友好的・中立的なキャラクターを表現し、会話、取引、クエストなどの
    インタラクション機能を提供します。プレイヤーとの相互作用を通じて
    ゲーム世界の豊かさを演出します。

    Attributes
    ----------
        char: 表示文字
        color: 表示色（RGB）
        disposition: NPC の態度
        npc_type: NPC の種類
        dialogue_id: 会話データの識別子
        inventory: 所持品・商品リスト
        quest_ids: 関連するクエストID

    """

    def __init__(
        self,
        char: str,
        x: int,
        y: int,
        name: str,
        level: int,
        hp: int,
        max_hp: int,
        attack: int,
        defense: int,
        color: tuple[int, int, int],
        disposition: NPCDisposition,
        npc_type: NPCType,
        dialogue_id: str,
        inventory: Inventory | None = None,
        quest_ids: list[str] | None = None,
    ) -> None:
        """
        NPCの初期化。

        Args:
        ----
            char: 表示文字
            x: NPCのX座標
            y: NPCのY座標
            name: NPC名
            level: NPCレベル
            hp: 現在のHP
            max_hp: 最大HP
            attack: 攻撃力
            defense: 防御力
            color: 表示色（RGB）
            disposition: NPC の態度
            npc_type: NPC の種類
            dialogue_id: 会話データの識別子
            inventory: 所持品・商品リスト
            quest_ids: 関連するクエストID

        """
        # 基底クラスの初期化（NPCは基本的に非敵対的）
        is_hostile = disposition == NPCDisposition.HOSTILE
        super().__init__(x, y, name, hp, max_hp, attack, defense, level, is_hostile)

        # NPC固有の属性
        self.char = char
        self.color = color
        self.disposition = disposition
        self.npc_type = npc_type
        self.dialogue_id = dialogue_id
        self.inventory = inventory
        self.quest_ids = quest_ids or []

        # システムの初期化
        self.status_effects = StatusEffectManager()

        # 会話・取引の状態管理
        self.dialogue_state: dict[str, Any] = {}  # 会話の進行状況
        self.last_interaction_turn: int = 0  # 最後の相互作用ターン

    def can_trade(self) -> bool:
        """
        取引可能かどうかを判定。

        Returns
        -------
            取引可能な場合はTrue

        """
        return (
            self.npc_type == NPCType.MERCHANT
            and self.disposition in [NPCDisposition.FRIENDLY, NPCDisposition.NEUTRAL]
            and self.inventory is not None
        )

    def can_talk(self) -> bool:
        """
        会話可能かどうかを判定。

        Returns
        -------
            会話可能な場合はTrue

        """
        return (
            self.disposition in [NPCDisposition.FRIENDLY, NPCDisposition.NEUTRAL]
            and self.dialogue_id is not None
        )

    def has_quest(self, quest_id: str) -> bool:
        """
        指定されたクエストを持っているかどうかを判定。

        Args:
        ----
            quest_id: クエストID

        Returns:
        -------
            クエストを持っている場合はTrue

        """
        return quest_id in self.quest_ids

    def add_quest(self, quest_id: str) -> None:
        """
        クエストを追加。

        Args:
        ----
            quest_id: 追加するクエストID

        """
        if quest_id not in self.quest_ids:
            self.quest_ids.append(quest_id)

    def remove_quest(self, quest_id: str) -> None:
        """
        クエストを削除。

        Args:
        ----
            quest_id: 削除するクエストID

        """
        if quest_id in self.quest_ids:
            self.quest_ids.remove(quest_id)

    def get_dialogue_state(self, key: str, default: Any = None) -> Any:
        """
        会話状態を取得。

        Args:
        ----
            key: 状態のキー
            default: デフォルト値

        Returns:
        -------
            会話状態の値

        """
        return self.dialogue_state.get(key, default)

    def set_dialogue_state(self, key: str, value: Any) -> None:
        """
        会話状態を設定。

        Args:
        ----
            key: 状態のキー
            value: 設定する値

        """
        self.dialogue_state[key] = value

    def update_interaction_turn(self, turn: int) -> None:
        """
        最後の相互作用ターンを更新。

        Args:
        ----
            turn: 現在のターン数

        """
        self.last_interaction_turn = turn

    def get_interaction_cooldown(self, current_turn: int) -> int:
        """
        相互作用のクールダウン残り時間を取得。

        Args:
        ----
            current_turn: 現在のターン数

        Returns:
        -------
            クールダウン残り時間

        """
        if self.last_interaction_turn == 0:
            return 0  # 初回の場合はクールダウンなし
        return max(0, 3 - (current_turn - self.last_interaction_turn))

    def sell_item(self, item: Item) -> bool:
        """
        アイテムを売る（NPCが購入）。

        Args:
        ----
            item: 売るアイテム

        Returns:
        -------
            取引が成功した場合はTrue

        """
        if not self.can_trade() or not self.inventory:
            return False

        # 商人の場合、アイテムを買い取る
        if self.npc_type == NPCType.MERCHANT:
            self.inventory.add_item(item)
            return True

        return False

    def buy_item(self, item: Item) -> bool:
        """
        アイテムを買う（NPCが販売）。

        Args:
        ----
            item: 買うアイテム

        Returns:
        -------
            取引が成功した場合はTrue

        """
        if not self.can_trade() or not self.inventory:
            return False

        # 商人の場合、アイテムを販売する
        if self.npc_type == NPCType.MERCHANT:
            if item in self.inventory.items:
                self.inventory.remove_item(item)
                return True
            return False

        return False

    def get_greeting_message(self) -> str:
        """
        挨拶メッセージを取得。

        Returns
        -------
            挨拶メッセージ

        """
        if self.disposition == NPCDisposition.FRIENDLY:
            return f"Hello there, adventurer! I'm {self.name}."
        if self.disposition == NPCDisposition.NEUTRAL:
            return f"Greetings. I am {self.name}."
        return f"{self.name} glares at you suspiciously."

    def get_farewell_message(self) -> str:
        """
        別れのメッセージを取得。

        Returns
        -------
            別れのメッセージ

        """
        if self.disposition == NPCDisposition.FRIENDLY:
            return "Farewell, and may fortune favor you!"
        if self.disposition == NPCDisposition.NEUTRAL:
            return "Until we meet again."
        return f"{self.name} turns away coldly."

    def update_status_effects(self, context) -> None:
        """
        状態異常のターン経過処理。

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
            状態異常が存在する場合はTrue

        """
        return self.status_effects.has_effect(name)

    def __str__(self) -> str:
        """NPCの文字列表現を取得。"""
        return f"{self.name} ({self.npc_type.value})"

    def __repr__(self) -> str:
        """NPCの詳細な文字列表現を取得。"""
        return (
            f"NPC(name={self.name}, type={self.npc_type.value}, "
            f"disposition={self.disposition.value}, pos=({self.x}, {self.y}))"
        )
