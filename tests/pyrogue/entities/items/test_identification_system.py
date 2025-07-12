#!/usr/bin/env python3
"""
識別システムのテスト用スクリプト
"""

from pyrogue.entities.actors.player import Player
from pyrogue.entities.items.effects import HEAL_LIGHT, IDENTIFY
from pyrogue.entities.items.item import Potion, Ring, Scroll


def test_identification_system():
    """識別システムのテスト"""
    print("=== 識別システムテスト開始 ===")

    # プレイヤーを作成
    player = Player(x=10, y=10)
    print(f"プレイヤー作成: {player.name}")

    # 未識別アイテムを作成
    potion = Potion(x=0, y=0, name="Healing Potion", effect=HEAL_LIGHT)
    scroll = Scroll(x=0, y=0, name="Scroll of Identify", effect=IDENTIFY)
    ring = Ring(x=0, y=0, name="Ring of Strength", effect="strength", bonus=2)

    print("\n=== 未識別アイテム作成 ===")
    print(f"ポーション: {potion.name} (タイプ: {potion.item_type})")
    print(f"巻物: {scroll.name} (タイプ: {scroll.item_type})")
    print(f"指輪: {ring.name} (タイプ: {ring.item_type})")

    # インベントリに追加
    player.inventory.add_item(potion)
    player.inventory.add_item(scroll)
    player.inventory.add_item(ring)

    print("\n=== 未識別状態での表示名 ===")
    print(f"ポーション: '{potion.get_display_name(player.identification)}'")
    print(f"巻物: '{scroll.get_display_name(player.identification)}'")
    print(f"指輪: '{ring.get_display_name(player.identification)}'")

    # 識別状態をチェック
    print("\n=== 識別状態チェック ===")
    print(
        f"ポーション識別済み: {player.identification.is_identified(potion.name, potion.item_type)}"
    )
    print(
        f"巻物識別済み: {player.identification.is_identified(scroll.name, scroll.item_type)}"
    )
    print(
        f"指輪識別済み: {player.identification.is_identified(ring.name, ring.item_type)}"
    )

    # ポーションを識別
    print("\n=== ポーション識別 ===")
    was_identified = player.identification.identify_item(potion.name, potion.item_type)
    print(f"識別成功: {was_identified}")
    if was_identified:
        msg = player.identification.get_identification_message(
            potion.name, potion.item_type
        )
        print(f"識別メッセージ: {msg}")

    # 識別後の表示名
    print("\n=== 識別後の表示名 ===")
    print(f"ポーション: '{potion.get_display_name(player.identification)}'")
    print(f"巻物: '{scroll.get_display_name(player.identification)}'")
    print(f"指輪: '{ring.get_display_name(player.identification)}'")

    # 識別の巻物で全て識別
    print("\n=== 識別の巻物で全識別 ===")
    scroll_identified = player.identification.identify_item(
        scroll.name, scroll.item_type
    )
    ring_identified = player.identification.identify_item(ring.name, ring.item_type)
    print(f"巻物識別: {scroll_identified}")
    print(f"指輪識別: {ring_identified}")

    # 最終的な表示名
    print("\n=== 最終的な表示名 ===")
    print(f"ポーション: '{potion.get_display_name(player.identification)}'")
    print(f"巻物: '{scroll.get_display_name(player.identification)}'")
    print(f"指輪: '{ring.get_display_name(player.identification)}'")

    print("\n=== 識別システムテスト完了 ===")


if __name__ == "__main__":
    test_identification_system()
