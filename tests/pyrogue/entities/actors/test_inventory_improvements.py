"""Inventory improvements test module."""

import pytest

from pyrogue.entities.actors.inventory import Inventory
from pyrogue.entities.items.effects import HealingEffect
from pyrogue.entities.items.item import Potion


def test_remove_item_error_handling():
    """remove_itemメソッドのエラーハンドリングをテスト"""
    inventory = Inventory()

    # テスト用ポーション作成
    potion = Potion(0, 0, "Test Potion", HealingEffect(heal_amount=10))
    inventory.add_item(potion)

    # 正常ケース
    removed = inventory.remove_item(potion, 1)
    assert removed == 1

    # 無効なカウント（0）
    with pytest.raises(ValueError, match="Invalid count: 0"):
        inventory.remove_item(potion, 0)

    # 無効なカウント（負数）
    with pytest.raises(ValueError, match="Invalid count: -1"):
        inventory.remove_item(potion, -1)


def test_remove_item_return_values():
    """remove_itemメソッドの戻り値をテスト"""
    inventory = Inventory()

    # 3個のスタック可能アイテムを作成
    for _ in range(3):
        potion = Potion(0, 0, "Test Potion", HealingEffect(heal_amount=10))
        inventory.add_item(potion)

    healing_potion = inventory.items[0]
    assert healing_potion.stack_count == 3

    # 1個削除
    removed = inventory.remove_item(healing_potion, 1)
    assert removed == 1
    assert healing_potion.stack_count == 2

    # 5個削除（実際は2個しかない）
    removed = inventory.remove_item(healing_potion, 5)
    assert removed == 2  # 実際に削除された数量
    assert len(inventory.items) == 0  # アイテム完全削除

    # 存在しないアイテム削除
    nonexistent_potion = Potion(0, 0, "Nonexistent", HealingEffect(heal_amount=10))
    removed = inventory.remove_item(nonexistent_potion, 1)
    assert removed == 0


def test_remove_item_equipment_handling():
    """装備中アイテムの削除処理をテスト"""
    from pyrogue.entities.items.item import Weapon

    inventory = Inventory()

    # 武器を作成して装備
    weapon = Weapon(0, 0, "Test Sword", 5)
    inventory.add_item(weapon)
    inventory.equip(weapon)

    # 装備確認
    assert inventory.equipped["weapon"] == weapon

    # 武器を削除
    removed = inventory.remove_item(weapon, 1)
    assert removed == 1
    assert len(inventory.items) == 0
    # 修正: remove_item()では装備スロットはクリアしない（別途unequip()が必要）
    assert inventory.equipped["weapon"] is weapon  # 装備スロットは保持される


def test_stack_behavior_comprehensive():
    """包括的なスタック動作テスト"""
    inventory = Inventory()

    # 5個のポーションを追加
    for _ in range(5):
        potion = Potion(0, 0, "Healing Potion", HealingEffect(heal_amount=12))
        inventory.add_item(potion)

    healing_potion = inventory.items[0]
    assert healing_potion.stack_count == 5

    # 部分削除テスト
    removed = inventory.remove_item(healing_potion, 2)
    assert removed == 2
    assert healing_potion.stack_count == 3
    assert len(inventory.items) == 1

    # 残り全削除テスト
    removed = inventory.remove_item(healing_potion, 3)
    assert removed == 3
    assert len(inventory.items) == 0


def test_drop_item_functionality():
    """新しいdrop_itemメソッドのテスト"""
    from pyrogue.entities.items.item import Weapon

    inventory = Inventory()

    # 武器を作成して装備
    weapon = Weapon(0, 0, "Test Sword", 5)
    inventory.add_item(weapon)
    inventory.equip(weapon)

    # 装備中の武器をドロップ
    success, dropped_count, message = inventory.drop_item(weapon)

    assert success is True
    assert dropped_count == 1
    assert "You first unequip" in message
    assert "You drop the" in message
    assert len(inventory.items) == 0
    assert inventory.equipped["weapon"] is None


def test_drop_item_cursed():
    """呪われたアイテムのドロップテスト"""
    from pyrogue.entities.items.item import Weapon

    inventory = Inventory()

    # 呪われた武器を作成
    weapon = Weapon(0, 0, "Cursed Sword", 5)
    weapon.cursed = True
    inventory.add_item(weapon)
    inventory.equip(weapon)

    # 呪われた武器のドロップ試行
    success, dropped_count, message = inventory.drop_item(weapon)

    assert success is False
    assert dropped_count == 0
    assert "cursed" in message
    assert len(inventory.items) == 1
    assert inventory.equipped["weapon"] is weapon


def test_can_drop_item():
    """can_drop_itemメソッドのテスト"""
    from pyrogue.entities.items.item import Weapon

    inventory = Inventory()

    # 通常の武器
    weapon = Weapon(0, 0, "Test Sword", 5)
    inventory.add_item(weapon)

    can_drop, error_msg = inventory.can_drop_item(weapon)
    assert can_drop is True
    assert error_msg is None

    # 呪われた武器を装備
    weapon.cursed = True
    inventory.equip(weapon)

    can_drop, error_msg = inventory.can_drop_item(weapon)
    assert can_drop is False
    assert "cursed" in error_msg


def test_drop_item_stackable():
    """スタック可能アイテムのドロップテスト"""
    inventory = Inventory()

    # スタック可能アイテムを5個追加
    for _ in range(5):
        potion = Potion(0, 0, "Healing Potion", HealingEffect(heal_amount=10))
        inventory.add_item(potion)

    healing_potion = inventory.items[0]
    assert healing_potion.stack_count == 5

    # 3個をドロップ
    success, dropped_count, message = inventory.drop_item(healing_potion, 3)

    assert success is True
    assert dropped_count == 3
    assert "You drop 3" in message
    assert healing_potion.stack_count == 2
    assert len(inventory.items) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
