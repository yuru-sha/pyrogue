"""Item effect system using command and strategy patterns."""

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pyrogue.entities.actors.player import Player
    from pyrogue.map.dungeon import Dungeon
    from pyrogue.ui.screens.game_screen import GameScreen

from pyrogue.entities.actors.status_effects import (
    ConfusionEffect,
    HallucinationEffect,
    ParalysisEffect,
    PoisonEffect,
)


def _add_message_safe(context, message: str) -> None:
    """コンテキストに安全にメッセージを追加するヘルパー関数。"""
    if hasattr(context, "add_message"):
        context.add_message(message)
    elif hasattr(context, "game_screen") and hasattr(
        context.game_screen, "message_log"
    ):
        context.game_screen.message_log.append(message)


def _get_floor_data_safe(context):
    """コンテキストから安全にフロアデータを取得するヘルパー関数。"""
    if hasattr(context, "dungeon_manager"):
        return context.dungeon_manager.get_current_floor_data()
    elif hasattr(context, "dungeon"):
        return context.dungeon
    return None


class EffectContext(Protocol):
    """Context protocol defining what effects can access."""

    @property
    def player(self) -> "Player":
        """Access to the player object."""
        ...

    @property
    def dungeon(self) -> "Dungeon":
        """Access to the current dungeon."""
        ...

    @property
    def game_screen(self) -> "GameScreen":
        """Access to the game screen for UI updates."""
        ...

    def add_message(
        self, message: str, color: tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        """Add a message to the game log."""
        ...


class Effect(ABC):
    """Abstract base class for all item effects."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def apply(self, context: EffectContext) -> bool:
        """Apply the effect. Returns True if successful, False otherwise."""

    def can_apply(self, context: EffectContext) -> bool:
        """Check if the effect can be applied in current context."""
        return True


class InstantEffect(Effect):
    """Base class for effects that apply immediately."""


class HealingEffect(InstantEffect):
    """Heals the player for a specified amount."""

    def __init__(self, heal_amount: int) -> None:
        super().__init__(name="Healing", description=f"Restores {heal_amount} HP")
        self.heal_amount = heal_amount

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        old_hp = player.hp
        player.heal(self.heal_amount)
        actual_heal = player.hp - old_hp

        if actual_heal > 0:
            _add_message_safe(context, f"You feel better! (+{actual_heal} HP)")
            return True
        _add_message_safe(context, "You are already at full health.")
        return False


class TeleportEffect(InstantEffect):
    """Teleports the player to a random location."""

    def __init__(self) -> None:
        super().__init__(
            name="Teleport", description="Instantly moves you to a random location"
        )

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        floor_data = _get_floor_data_safe(context)

        if not floor_data:
            return False

        # Find a random walkable tile
        max_attempts = 100
        height, width = floor_data.tiles.shape
        for _ in range(max_attempts):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            if (floor_data.tiles[y][x].walkable and 
                not floor_data.monster_spawner.get_monster_at(x, y)):
                old_x, old_y = player.x, player.y
                player.x, player.y = x, y

                _add_message_safe(
                    context, f"You teleport from ({old_x}, {old_y}) to ({x}, {y})!"
                )
                return True

        _add_message_safe(context, "The teleportation fails!")
        return False


class MagicMappingEffect(InstantEffect):
    """Reveals the entire dungeon map."""

    def __init__(self) -> None:
        super().__init__(
            name="Magic Mapping", description="Reveals the entire dungeon layout"
        )

    def apply(self, context: EffectContext) -> bool:
        floor_data = _get_floor_data_safe(context)

        if not floor_data:
            return False

        # Reveal all tiles
        height, width = floor_data.tiles.shape
        for y in range(height):
            for x in range(width):
                floor_data.explored[y][x] = True

        _add_message_safe(context, "The dungeon layout is revealed to your mind!")
        return True


class IdentifyEffect(InstantEffect):
    """Identifies all items in the player's inventory."""

    def __init__(self) -> None:
        super().__init__(
            name="Identify", description="Reveals the true nature of your items"
        )

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        unidentified_count = 0

        # 新しい識別システムを使用
        for item in player.inventory.items:
            if hasattr(item, "item_type") and hasattr(item, "name"):
                # 未識別のアイテムのみ処理
                if not player.identification.is_identified(item.name, item.item_type):
                    was_identified = player.identification.identify_item(
                        item.name, item.item_type
                    )
                    if was_identified:
                        unidentified_count += 1
                        # 識別メッセージを追加
                        msg = player.identification.get_identification_message(
                            item.name, item.item_type
                        )
                        _add_message_safe(context, msg)

        if unidentified_count > 0:
            _add_message_safe(context, f"You identify {unidentified_count} item(s)!")
        else:
            _add_message_safe(context, "All your items are already known to you.")

        return True


class NutritionEffect(InstantEffect):
    """Restores hunger/nutrition."""

    def __init__(self, nutrition_value: int) -> None:
        super().__init__(
            name="Nutrition", description=f"Restores {nutrition_value} hunger"
        )
        self.nutrition_value = nutrition_value

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        old_hunger = player.hunger
        player.eat_food(self.nutrition_value)

        hunger_gained = player.hunger - old_hunger
        if hunger_gained > 0:
            _add_message_safe(context, f"You feel satisfied. (+{hunger_gained} hunger)")
            return True
        _add_message_safe(context, "You are already full.")
        return False


class RemoveCurseEffect(InstantEffect):
    """Removes curse from all items in the player's inventory."""

    def __init__(self) -> None:
        super().__init__(
            name="Remove Curse", description="Removes the curse from all your items"
        )

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        cursed_count = 0

        # Remove curse from all items in inventory
        for item in player.inventory.items:
            if item.cursed:
                item.cursed = False
                cursed_count += 1

        # Remove curse from all equipped items
        for slot_item in player.inventory.equipped.values():
            if slot_item and slot_item.cursed:
                slot_item.cursed = False
                cursed_count += 1

        if cursed_count > 0:
            _add_message_safe(
                context, f"You feel the curse lift from {cursed_count} item(s)!"
            )
        else:
            _add_message_safe(
                context, "You don't feel any curses upon your belongings."
            )

        return True


class EnchantWeaponEffect(InstantEffect):
    """Enchants the currently equipped weapon."""

    def __init__(self) -> None:
        super().__init__(
            name="Enchant Weapon", description="Magically enhances your weapon"
        )

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        weapon = player.inventory.get_equipped_weapon()

        if not weapon:
            _add_message_safe(
                context, "You need to be wielding a weapon to enchant it!"
            )
            return False

        # Check enchantment limit (max +9)
        if weapon.enchantment >= 9:
            _add_message_safe(
                context, "Your weapon glows briefly, but nothing happens."
            )
            return False

        weapon.enchantment += 1
        enchant_text = f"+{weapon.enchantment}" if weapon.enchantment > 0 else ""
        _add_message_safe(
            context,
            f"Your {weapon.name} glows with magical energy! (now {enchant_text} {weapon.name})",
        )
        return True


class EnchantArmorEffect(InstantEffect):
    """Enchants the currently equipped armor."""

    def __init__(self) -> None:
        super().__init__(
            name="Enchant Armor", description="Magically enhances your armor"
        )

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        armor = player.inventory.get_equipped_armor()

        if not armor:
            _add_message_safe(context, "You need to be wearing armor to enchant it!")
            return False

        # Check enchantment limit (max +9)
        if armor.enchantment >= 9:
            _add_message_safe(
                context, "Your armor gleams briefly, but nothing happens."
            )
            return False

        armor.enchantment += 1
        enchant_text = f"+{armor.enchantment}" if armor.enchantment > 0 else ""
        _add_message_safe(
            context,
            f"Your {armor.name} shimmers with protective magic! (now {enchant_text} {armor.name})",
        )
        return True


class LightEffect(InstantEffect):
    """Creates a magical light that expands the player's vision for a limited time."""

    def __init__(self, duration: int = 50, radius: int = 15) -> None:
        super().__init__(
            name="Light", description=f"Illuminates a wide area for {duration} turns"
        )
        self.duration = duration
        self.radius = radius

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        player.apply_light_effect(self.duration, self.radius)

        _add_message_safe(
            context, "A brilliant light surrounds you, expanding your vision!"
        )
        return True


class StatusEffectApplication(InstantEffect):
    """Applies a status effect to the player."""

    def __init__(
        self, status_effect_class, name: str, description: str, **kwargs
    ) -> None:
        super().__init__(name=name, description=description)
        self.status_effect_class = status_effect_class
        self.kwargs = kwargs

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        status_effect = self.status_effect_class(**self.kwargs)

        player.status_effects.add_effect(status_effect)

        _add_message_safe(context, f"You are affected by {status_effect.name}!")
        return True


class PoisonPotionEffect(StatusEffectApplication):
    """Poisons the player."""

    def __init__(self, duration: int = 5, damage: int = 2) -> None:
        super().__init__(
            status_effect_class=PoisonEffect,
            name="Poison",
            description=f"Poisons you for {duration} turns",
            duration=duration,
            damage=damage,
        )


class ParalysisPotionEffect(StatusEffectApplication):
    """Paralyzes the player."""

    def __init__(self, duration: int = 3) -> None:
        super().__init__(
            status_effect_class=ParalysisEffect,
            name="Paralysis",
            description=f"Paralyzes you for {duration} turns",
            duration=duration,
        )


class ConfusionPotionEffect(StatusEffectApplication):
    """Confuses the player."""

    def __init__(self, duration: int = 4) -> None:
        super().__init__(
            status_effect_class=ConfusionEffect,
            name="Confusion",
            description=f"Confuses you for {duration} turns",
            duration=duration,
        )


class HallucinationPotionEffect(StatusEffectApplication):
    """Causes hallucinations in the player."""

    def __init__(self, duration: int = 8) -> None:
        super().__init__(
            status_effect_class=HallucinationEffect,
            name="Hallucination",
            description=f"Causes hallucinations for {duration} turns",
            duration=duration,
        )


# Pre-defined common effects
HEAL_LIGHT = HealingEffect(25)
HEAL_MEDIUM = HealingEffect(50)
HEAL_FULL = HealingEffect(999)
TELEPORT = TeleportEffect()
MAGIC_MAPPING = MagicMappingEffect()
IDENTIFY = IdentifyEffect()
REMOVE_CURSE = RemoveCurseEffect()
ENCHANT_WEAPON = EnchantWeaponEffect()
ENCHANT_ARMOR = EnchantArmorEffect()
LIGHT = LightEffect()
FOOD_RATION = NutritionEffect(200)
FOOD_BREAD = NutritionEffect(100)
FOOD_APPLE = NutritionEffect(50)
POISON_POTION = PoisonPotionEffect()
PARALYSIS_POTION = ParalysisPotionEffect()
CONFUSION_POTION = ConfusionPotionEffect()
HALLUCINATION_POTION = HallucinationPotionEffect()
