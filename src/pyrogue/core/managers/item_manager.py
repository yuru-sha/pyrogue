"""
アイテム関連の処理を管理するマネージャー。

GameLogicからアイテム処理を分離し、
より単純で保守しやすい構造にします。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext
    from pyrogue.entities.items.item import Item


class ItemManager:
    """
    アイテム関連の処理を担当するマネージャー。

    責務:
    - アイテムの取得処理
    - アイテムの使用処理
    - アイテムのドロップ処理
    - インベントリの管理
    """

    def __init__(self, context: GameContext) -> None:
        """
        ItemManagerを初期化。

        Args:
        ----
            context: 共有ゲームコンテキスト

        """
        self.context = context

    def handle_get_item(self) -> str | None:
        """
        プレイヤーの位置にあるアイテムを取得。

        Returns
        -------
            取得したアイテムの名前、取得できない場合None

        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()

        if not floor_data:
            self.context.add_message("No items to get here.")
            return None

        # プレイヤーの位置にあるアイテムを探す
        items_at_position = [item for item in floor_data.items if item.x == player.x and item.y == player.y]

        if not items_at_position:
            self.context.add_message("No items to get here.")
            return None

        # 複数アイテムがある場合は最初のものを取得
        item = items_at_position[0]

        # ゴールドの場合は特別処理
        if hasattr(item, "item_type") and item.item_type == "GOLD":
            amount = getattr(item, "amount", 1)
            player.gold += amount
            floor_data.items.remove(item)
            self.context.add_message(f"You pick up {amount} gold pieces.")
            return f"{amount} gold pieces"

        # 通常のアイテムはインベントリに追加を試行
        if self._try_add_to_inventory(item):
            # フロアからアイテムを削除
            floor_data.items.remove(item)

            # 取得メッセージ
            self.context.add_message(f"You pick up the {item.name}.")
            return item.name

        return None

    def _try_add_to_inventory(self, item: Item) -> bool:
        """
        インベントリにアイテムを追加を試行。

        Args:
        ----
            item: 追加するアイテム

        Returns:
        -------
            追加が成功した場合True

        """
        inventory = self.context.inventory

        # アイテムをインベントリに追加（add_itemがFalseを返す場合は容量不足）
        if not inventory.add_item(item):
            self.context.add_message("Your inventory is full!")
            return False

        return True

    def _get_item_by_name(self, item_name: str):
        """
        アイテム名でインベントリからアイテムを検索。

        Args:
        ----
            item_name: 検索するアイテム名

        Returns:
        -------
            見つかったアイテム、なければNone

        """
        inventory = self.context.inventory

        # インベントリのアイテムリストを走査
        for item in inventory.items:
            if item.name.lower() == item_name.lower():
                return item

        return None

    def handle_use_item(self, item_name: str) -> bool:
        """
        アイテムの使用処理。

        Args:
        ----
            item_name: 使用するアイテムの名前

        Returns:
        -------
            使用が成功した場合True

        """
        inventory = self.context.inventory

        # インベントリからアイテムを検索
        item = self._get_item_by_name(item_name)

        if not item:
            self.context.add_message(f"You don't have a {item_name}.")
            return False

        # Player.use_item()を使用して統一された処理を行う
        try:
            # 使用メッセージを表示（"You read", "You drink", "You eat"など）
            if hasattr(item, "use"):
                use_message = item.use()
                self.context.add_message(use_message)

            # Player.use_itemで効果適用とアイテム削除を実行
            success = self.context.player.use_item(item, self.context)

            if success:
                # 使用成功時の追加処理
                return True
            # 使用失敗時の処理
            self.context.add_message(f"The {item_name} has no effect.")
            return False

        except Exception as e:
            self.context.add_message(f"Failed to use {item_name}: {e!s}")
            return False

    def _handle_item_use_success(self, item: Item) -> None:
        """
        アイテム使用成功時の処理。

        Args:
        ----
            item: 使用したアイテム

        """
        inventory = self.context.inventory

        # 消耗品の場合はインベントリから削除
        if hasattr(item, "consumable") and item.consumable:
            inventory.remove_item(item)
            self.context.add_message(f"You used the {item.name}.")
        else:
            self.context.add_message(f"You used the {item.name}.")

    def _handle_item_use_failure(self, item: Item) -> None:
        """
        アイテム使用失敗時の処理。

        Args:
        ----
            item: 使用を試行したアイテム

        """
        self.context.add_message(f"You couldn't use the {item.name}.")

    def handle_drop_item(self, item_name: str) -> bool:
        """
        アイテムのドロップ処理。

        Args:
        ----
            item_name: ドロップするアイテムの名前

        Returns:
        -------
            ドロップが成功した場合True

        """
        inventory = self.context.inventory

        # インベントリからアイテムを検索
        item = self._get_item_by_name(item_name)

        if not item:
            self.context.add_message(f"You don't have a {item_name}.")
            return False

        # 装備中のアイテムの場合は装備解除
        if inventory.is_equipped(item):
            # 呪われたアイテムのチェック
            if hasattr(item, "cursed") and item.cursed:
                self.context.add_message(f"You can't drop the {item_name}! It's cursed!")
                return False

            # 装備解除
            inventory.unequip(item)
            self.context.add_message(f"You unequip the {item_name}.")

        # インベントリから削除（スタック可能アイテムは全スタック削除）
        if item.stackable and item.stack_count > 1:
            inventory.remove_item(item, item.stack_count)
            self.context.add_message(f"You drop {item.stack_count} {item_name}.")
        else:
            inventory.remove_item(item)
            self.context.add_message(f"You drop the {item_name}.")

        # フロアに配置
        self._place_item_on_floor(item)
        return True

    def _place_item_on_floor(self, item: Item) -> None:
        """
        アイテムをフロアに配置。

        Args:
        ----
            item: 配置するアイテム

        """
        player = self.context.player
        floor_data = self.context.dungeon_manager.get_current_floor_data()

        if not floor_data:
            return

        # プレイヤーの位置にアイテムを配置
        item.x = player.x
        item.y = player.y
        floor_data.items.append(item)

    def handle_equip_item(self, item_name: str) -> bool:
        """
        アイテムの装備処理。

        Args:
        ----
            item_name: 装備するアイテムの名前

        Returns:
        -------
            装備が成功した場合True

        """
        inventory = self.context.inventory

        # インベントリからアイテムを検索
        item = self._get_item_by_name(item_name)

        if not item:
            self.context.add_message(f"You don't have a {item_name}.")
            return False

        # 装備可能かチェック
        if not hasattr(item, "equippable") or not item.equippable:
            self.context.add_message(f"You can't equip the {item_name}.")
            return False

        # 装備処理
        old_item = inventory.equip(item)
        if old_item is not None:
            self.context.add_message(f"You unequip the {old_item.name} and equip the {item_name}.")
        else:
            self.context.add_message(f"You equip the {item_name}.")
        return True

    def handle_unequip_item(self, item_name: str) -> bool:
        """
        アイテムの装備解除処理。

        Args:
        ----
            item_name: 装備解除するアイテムの名前

        Returns:
        -------
            装備解除が成功した場合True

        """
        inventory = self.context.inventory

        # インベントリからアイテムを検索
        item = self._get_item_by_name(item_name)

        if not item:
            self.context.add_message(f"You don't have a {item_name}.")
            return False

        # 装備中かチェック
        if not inventory.is_equipped(item):
            self.context.add_message(f"The {item_name} is not equipped.")
            return False

        # 呪われたアイテムのチェック
        if hasattr(item, "cursed") and item.cursed:
            self.context.add_message(f"You can't unequip the {item_name}! It's cursed!")
            return False

        # 装備解除処理（スロットを特定する必要がある）
        slot = self._get_equipment_slot(item)
        if slot:
            unequipped_item = inventory.unequip(slot)
            if unequipped_item:
                self.context.add_message(f"You unequip the {item_name}.")
                return True

        self.context.add_message(f"You couldn't unequip the {item_name}.")
        return False

    def _get_equipment_slot(self, item) -> str | None:
        """
        アイテムの装備スロットを特定。

        Args:
        ----
            item: アイテム

        Returns:
        -------
            装備スロット名、見つからない場合None

        """
        inventory = self.context.inventory

        # 各スロットをチェック
        for slot in ["weapon", "armor", "ring_left", "ring_right"]:
            if hasattr(inventory, slot):
                equipped_item = getattr(inventory, slot)
                if equipped_item == item:
                    return slot

        return None

    def get_items_at_position(self, x: int, y: int) -> list[Item]:
        """
        指定位置にあるアイテムのリストを取得。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            指定位置にあるアイテムのリスト

        """
        floor_data = self.context.dungeon_manager.get_current_floor_data()

        if not floor_data:
            return []

        return [item for item in floor_data.items if item.x == x and item.y == y]

    def get_total_items_at_position(self, x: int, y: int) -> int:
        """
        指定位置にあるアイテムの総数を取得。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            指定位置にあるアイテムの総数

        """
        return len(self.get_items_at_position(x, y))
