"""アイテムID→オブジェクト生成ファクトリーシステム"""


from pyrogue.entities.items.amulet import AmuletOfYendor
from pyrogue.entities.items.effects import (
    ConfusionPotionEffect,
    EnchantArmorEffect,
    EnchantWeaponEffect,
    HealingEffect,
    IdentifyEffect,
    LightEffect,
    LightningWandEffect,
    LightWandEffect,
    MagicMappingEffect,
    MagicMissileWandEffect,
    NothingWandEffect,
    NutritionEffect,
    ParalysisPotionEffect,
    PoisonPotionEffect,
    RemoveCurseEffect,
    TeleportEffect,
)
from pyrogue.entities.items.item import Armor, Food, Gold, Potion, Ring, Scroll, Wand, Weapon


class ItemFactory:
    """アイテムIDからアイテムオブジェクトを生成するファクトリー"""

    # アイテムID範囲定義
    WEAPONS_RANGE = (100, 199)
    ARMORS_RANGE = (200, 299)
    POTIONS_RANGE = (300, 399)
    SCROLLS_RANGE = (400, 499)
    RINGS_RANGE = (500, 599)
    WANDS_RANGE = (600, 699)
    FOODS_RANGE = (700, 799)
    SPECIAL_RANGE = (800, 899)

    @staticmethod
    def create_by_id(item_id: int, x: int = 0, y: int = 0):
        """アイテムIDからアイテムオブジェクトを生成"""
        item = None

        # 武器 (100-199)
        if item_id == 101:  # Dagger
            item = Weapon(x, y, "Dagger", 2)
        elif item_id == 102:  # Mace
            item = Weapon(x, y, "Mace", 2)
        elif item_id == 103:  # Long Sword
            item = Weapon(x, y, "Long Sword", 4)
        elif item_id == 104:  # Short Bow
            item = Weapon(x, y, "Short Bow", 3)
        elif item_id == 105:  # Battle Axe
            item = Weapon(x, y, "Battle Axe", 6)
        elif item_id == 106:  # Two-Handed Sword
            item = Weapon(x, y, "Two-Handed Sword", 8)

        # 防具 (200-299)
        elif item_id == 201:  # Leather Armor
            item = Armor(x, y, "Leather Armor", 2)
        elif item_id == 202:  # Studded Leather
            item = Armor(x, y, "Studded Leather", 3)
        elif item_id == 203:  # Ring Mail
            item = Armor(x, y, "Ring Mail", 4)
        elif item_id == 204:  # Scale Mail
            item = Armor(x, y, "Scale Mail", 5)
        elif item_id == 205:  # Chain Mail
            item = Armor(x, y, "Chain Mail", 6)
        elif item_id == 206:  # Splint Mail
            item = Armor(x, y, "Splint Mail", 7)
        elif item_id == 207:  # Banded Mail
            item = Armor(x, y, "Banded Mail", 8)
        elif item_id == 208:  # Plate Mail
            item = Armor(x, y, "Plate Mail", 9)

        # ポーション (300-399)
        elif item_id == 301:  # Potion of Healing
            item = Potion(x, y, "Potion of Healing", HealingEffect(25))
        elif item_id == 302:  # Potion of Extra Healing
            item = Potion(x, y, "Potion of Extra Healing", HealingEffect(50))
        elif item_id == 303:  # Potion of Strength
            item = Potion(x, y, "Potion of Strength", HealingEffect(0))  # TODO: StrengthEffect
        elif item_id == 304:  # Potion of Restore Strength
            item = Potion(x, y, "Potion of Restore Strength", HealingEffect(0))  # TODO: RestoreStrengthEffect
        elif item_id == 305:  # Potion of Haste Self
            item = Potion(x, y, "Potion of Haste Self", HealingEffect(0))  # TODO: HasteEffect
        elif item_id == 306:  # Potion of See Invisible
            item = Potion(x, y, "Potion of See Invisible", HealingEffect(0))  # TODO: SeeInvisibleEffect
        elif item_id == 307:  # Potion of Poison
            item = Potion(x, y, "Potion of Poison", PoisonPotionEffect())
        elif item_id == 308:  # Potion of Paralysis
            item = Potion(x, y, "Potion of Paralysis", ParalysisPotionEffect())
        elif item_id == 309:  # Potion of Confusion
            item = Potion(x, y, "Potion of Confusion", ConfusionPotionEffect())

        # 巻物 (400-499)
        elif item_id == 401:  # Scroll of Identify
            item = Scroll(x, y, "Scroll of Identify", IdentifyEffect())
        elif item_id == 402:  # Scroll of Light
            item = Scroll(x, y, "Scroll of Light", LightEffect())
        elif item_id == 403:  # Scroll of Remove Curse
            item = Scroll(x, y, "Scroll of Remove Curse", RemoveCurseEffect())
        elif item_id == 404:  # Scroll of Enchant Weapon
            item = Scroll(x, y, "Scroll of Enchant Weapon", EnchantWeaponEffect())
        elif item_id == 405:  # Scroll of Enchant Armor
            item = Scroll(x, y, "Scroll of Enchant Armor", EnchantArmorEffect())
        elif item_id == 406:  # Scroll of Teleport
            item = Scroll(x, y, "Scroll of Teleport", TeleportEffect())
        elif item_id == 407:  # Scroll of Magic Mapping
            item = Scroll(x, y, "Scroll of Magic Mapping", MagicMappingEffect())

        # 指輪 (500-599)
        elif item_id == 501:  # Ring of Protection
            item = Ring(x, y, "Ring of Protection", "protection", 1)
        elif item_id == 502:  # Ring of Add Strength
            item = Ring(x, y, "Ring of Add Strength", "strength", 1)
        elif item_id == 503:  # Ring of Sustain Strength
            item = Ring(x, y, "Ring of Sustain Strength", "sustain", 1)
        elif item_id == 504:  # Ring of Searching
            item = Ring(x, y, "Ring of Searching", "search", 1)
        elif item_id == 505:  # Ring of See Invisible
            item = Ring(x, y, "Ring of See Invisible", "see_invisible", 1)
        elif item_id == 506:  # Ring of Regeneration
            item = Ring(x, y, "Ring of Regeneration", "regeneration", 1)

        # 杖 (600-699)
        elif item_id == 601:  # Wand of Magic Missiles
            item = Wand(x, y, "Wand of Magic Missiles", MagicMissileWandEffect(), 3)
        elif item_id == 602:  # Wand of Light
            item = Wand(x, y, "Wand of Light", LightWandEffect(), 3)
        elif item_id == 603:  # Wand of Lightning
            item = Wand(x, y, "Wand of Lightning", LightningWandEffect(), 3)
        elif item_id == 604:  # Wand of Fire
            item = Wand(x, y, "Wand of Fire", LightWandEffect(), 3)  # TODO: FireWandEffect
        elif item_id == 605:  # Wand of Cold
            item = Wand(x, y, "Wand of Cold", LightWandEffect(), 3)  # TODO: ColdWandEffect
        elif item_id == 606:  # Wand of Polymorph
            item = Wand(x, y, "Wand of Polymorph", NothingWandEffect(), 3)  # TODO: PolymorphWandEffect
        elif item_id == 607:  # Wand of Teleport Monster
            item = Wand(x, y, "Wand of Teleport Monster", NothingWandEffect(), 3)  # TODO: TeleportMonsterWandEffect
        elif item_id == 608:  # Wand of Slow Monster
            item = Wand(x, y, "Wand of Slow Monster", NothingWandEffect(), 3)  # TODO: SlowMonsterWandEffect
        elif item_id == 609:  # Wand of Haste Monster
            item = Wand(x, y, "Wand of Haste Monster", NothingWandEffect(), 3)  # TODO: HasteMonsterWandEffect
        elif item_id == 610:  # Wand of Sleep
            item = Wand(x, y, "Wand of Sleep", NothingWandEffect(), 3)  # TODO: SleepWandEffect
        elif item_id == 611:  # Wand of Drain Life
            item = Wand(x, y, "Wand of Drain Life", NothingWandEffect(), 3)  # TODO: DrainLifeWandEffect
        elif item_id == 612:  # Wand of Nothing
            item = Wand(x, y, "Wand of Nothing", NothingWandEffect(), 3)

        # 食料 (700-799)
        elif item_id == 701:  # Food Ration
            item = Food(x, y, "Food Ration", NutritionEffect(25))
        elif item_id == 702:  # Slime Mold
            item = Food(x, y, "Slime Mold", NutritionEffect(15))

        # 特殊アイテム (800-899)
        elif item_id == 801:  # Gold
            item = Gold(x, y, 1)
        elif item_id == 802:  # Amulet of Yendor
            item = AmuletOfYendor(x, y)

        # 不明なID
        else:
            raise ValueError(f"Unknown item ID: {item_id}")

        # 生成されたアイテムにIDを設定
        if item is not None:
            item.item_id = item_id
            return item
        raise ValueError(f"Failed to create item with ID: {item_id}")

    @staticmethod
    def get_id_by_name(name: str) -> int | None:
        """アイテム名からIDを取得（後方互換性用）"""
        name_to_id_map = {
            # 武器
            "Dagger": 101,
            "Mace": 102,
            "Long Sword": 103,
            "Short Bow": 104,
            "Battle Axe": 105,
            "Two-Handed Sword": 106,
            # 防具
            "Leather Armor": 201,
            "Studded Leather": 202,
            "Ring Mail": 203,
            "Scale Mail": 204,
            "Chain Mail": 205,
            "Splint Mail": 206,
            "Banded Mail": 207,
            "Plate Mail": 208,
            # ポーション
            "Potion of Healing": 301,
            "Potion of Extra Healing": 302,
            "Potion of Strength": 303,
            "Potion of Restore Strength": 304,
            "Potion of Haste Self": 305,
            "Potion of See Invisible": 306,
            "Potion of Poison": 307,
            "Potion of Paralysis": 308,
            "Potion of Confusion": 309,
            # 巻物
            "Scroll of Identify": 401,
            "Scroll of Light": 402,
            "Scroll of Remove Curse": 403,
            "Scroll of Enchant Weapon": 404,
            "Scroll of Enchant Armor": 405,
            "Scroll of Teleport": 406,
            "Scroll of Magic Mapping": 407,
            # 指輪
            "Ring of Protection": 501,
            "Ring of Add Strength": 502,
            "Ring of Sustain Strength": 503,
            "Ring of Searching": 504,
            "Ring of See Invisible": 505,
            "Ring of Regeneration": 506,
            # 杖
            "Wand of Magic Missiles": 601,
            "Wand of Light": 602,
            "Wand of Lightning": 603,
            "Wand of Fire": 604,
            "Wand of Cold": 605,
            "Wand of Polymorph": 606,
            "Wand of Teleport Monster": 607,
            "Wand of Slow Monster": 608,
            "Wand of Haste Monster": 609,
            "Wand of Sleep": 610,
            "Wand of Drain Life": 611,
            "Wand of Nothing": 612,
            # 食料
            "Food Ration": 701,
            "Slime Mold": 702,
            # 特殊
            "Gold": 801,
            "Amulet of Yendor": 802,
        }
        return name_to_id_map.get(name)
