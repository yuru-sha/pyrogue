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
    assert inventory.equipped["weapon"] is None  # 装備スロットもクリア


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
