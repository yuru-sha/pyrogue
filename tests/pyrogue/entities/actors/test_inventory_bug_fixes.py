"""
インベントリ装備システムのバグ修正テスト。

このモジュールは、報告されたバグが修正されていることを確認するためのテストを含みます。
"""


from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.items.item import Armor, Ring, Weapon


class TestInventoryBugFixes:
    """インベントリ装備システムのバグ修正テスト。"""

    def test_ring_equipment_does_not_disappear(self):
        """指輪装備時にインベントリから消失しないことを確認。"""
        inventory = Inventory()
        ring = Ring(0, 0, "Test Ring", "strength", 1)

        # インベントリに追加
        inventory.add_item(ring)
        assert ring in inventory.items

        # 装備実行
        old_item = inventory.equip(ring)

        # 装備成功確認
        assert inventory.is_equipped(ring)

        # 重要：装備後もインベントリに残る
        assert ring in inventory.items

        # 装備スロット確認
        assert inventory.equipped["ring_left"] is ring
        assert inventory.equipped["ring_right"] is None

    def test_ring_equipment_both_hands(self):
        """両手の指輪装備が正しく動作することを確認。"""
        inventory = Inventory()
        ring1 = Ring(0, 0, "Ring 1", "strength", 1)
        ring2 = Ring(0, 0, "Ring 2", "protection", 2)

        # 両方をインベントリに追加
        inventory.add_item(ring1)
        inventory.add_item(ring2)

        # 1つ目の指輪装備（左手）
        old_item = inventory.equip(ring1)
        assert old_item is None
        assert inventory.equipped["ring_left"] is ring1
        assert inventory.equipped["ring_right"] is None
        assert ring1 in inventory.items

        # 2つ目の指輪装備（右手）
        old_item = inventory.equip(ring2)
        assert old_item is None
        assert inventory.equipped["ring_left"] is ring1
        assert inventory.equipped["ring_right"] is ring2
        assert ring2 in inventory.items

    def test_armor_equipment_display_name_correct(self):
        """防具装備時の表示名が正しいことを確認。"""
        inventory = Inventory()
        armor = Armor(0, 0, "Chain Mail", 4)

        # インベントリに追加
        inventory.add_item(armor)

        # 装備実行
        old_item = inventory.equip(armor)

        # 装備成功確認
        assert inventory.is_equipped(armor)

        # 表示名が正しい
        assert armor.name == "Chain Mail"
        assert inventory.equipped["armor"] is armor
        assert inventory.equipped["armor"].name == "Chain Mail"

        # インベントリに残る
        assert armor in inventory.items

    def test_equipment_slot_identification(self):
        """装備スロットの識別が正しく動作することを確認。"""
        inventory = Inventory()

        ring_left = Ring(0, 0, "Left Ring", "strength", 1)
        ring_right = Ring(0, 0, "Right Ring", "protection", 2)
        armor = Armor(0, 0, "Test Armor", 3)
        weapon = Weapon(0, 0, "Test Weapon", 5)

        # 全てを追加・装備
        inventory.add_item(ring_left)
        inventory.add_item(ring_right)
        inventory.add_item(armor)
        inventory.add_item(weapon)

        inventory.equip(ring_left)
        inventory.equip(ring_right)
        inventory.equip(armor)
        inventory.equip(weapon)

        # スロット識別確認
        assert inventory.get_equipped_slot(ring_left) == "ring_left"
        assert inventory.get_equipped_slot(ring_right) == "ring_right"
        assert inventory.get_equipped_slot(armor) == "armor"
        assert inventory.get_equipped_slot(weapon) == "weapon"

    def test_armor_replacement_preserves_names(self):
        """防具交換時に名前が保持されることを確認。"""
        inventory = Inventory()
        armor1 = Armor(0, 0, "Leather Armor", 2)
        armor2 = Armor(0, 0, "Chain Mail", 4)

        inventory.add_item(armor1)
        inventory.add_item(armor2)

        # 1つ目の防具装備
        old_item = inventory.equip(armor1)
        assert old_item is None
        assert inventory.equipped["armor"] is armor1
        assert inventory.equipped["armor"].name == "Leather Armor"

        # 2つ目の防具装備（交換）
        old_item = inventory.equip(armor2)
        assert old_item is armor1
        assert old_item.name == "Leather Armor"
        assert inventory.equipped["armor"] is armor2
        assert inventory.equipped["armor"].name == "Chain Mail"

    def test_equipment_stays_in_inventory(self):
        """装備品がインベントリに残ることを確認。"""
        inventory = Inventory()

        ring = Ring(0, 0, "Test Ring", "strength", 1)
        armor = Armor(0, 0, "Test Armor", 3)
        weapon = Weapon(0, 0, "Test Weapon", 5)

        # 全てを追加
        inventory.add_item(ring)
        inventory.add_item(armor)
        inventory.add_item(weapon)

        initial_count = len(inventory.items)

        # 全て装備
        inventory.equip(ring)
        inventory.equip(armor)
        inventory.equip(weapon)

        # 装備後もインベントリ数は変わらない
        assert len(inventory.items) == initial_count

        # 全て装備されている
        assert inventory.is_equipped(ring)
        assert inventory.is_equipped(armor)
        assert inventory.is_equipped(weapon)

        # 全てインベントリに残っている
        assert ring in inventory.items
        assert armor in inventory.items
        assert weapon in inventory.items

    def test_equipment_with_cursed_items(self):
        """呪われたアイテムの装備解除制限確認。"""
        inventory = Inventory()

        # 呪われた指輪
        cursed_ring = Ring(0, 0, "Cursed Ring", "strength", -1)
        cursed_ring.cursed = True

        inventory.add_item(cursed_ring)

        # 装備可能
        inventory.equip(cursed_ring)
        assert inventory.is_equipped(cursed_ring)

        # 装備解除不可
        success, message = inventory.can_drop_item(cursed_ring)
        assert not success
        assert "cursed" in message.lower()

    def test_ring_equipment_order(self):
        """指輪装備の順序が正しいことを確認。"""
        inventory = Inventory()

        ring1 = Ring(0, 0, "First Ring", "strength", 1)
        ring2 = Ring(0, 0, "Second Ring", "protection", 2)
        ring3 = Ring(0, 0, "Third Ring", "dexterity", 3)

        inventory.add_item(ring1)
        inventory.add_item(ring2)
        inventory.add_item(ring3)

        # 1つ目：左手
        inventory.equip(ring1)
        assert inventory.equipped["ring_left"] is ring1
        assert inventory.equipped["ring_right"] is None

        # 2つ目：右手
        inventory.equip(ring2)
        assert inventory.equipped["ring_left"] is ring1
        assert inventory.equipped["ring_right"] is ring2

        # 3つ目：右手を交換
        old_item = inventory.equip(ring3)
        assert old_item is ring2
        assert inventory.equipped["ring_left"] is ring1
        assert inventory.equipped["ring_right"] is ring3
