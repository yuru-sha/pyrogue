"""Item effect system using command and strategy patterns."""

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pyrogue.entities.actors.player import Player
    from pyrogue.map.dungeon import Dungeon
    from pyrogue.ui.screens.game_screen import GameScreen


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


class Effect(ABC):
    """Abstract base class for all item effects."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def apply(self, context: EffectContext) -> bool:
        """Apply the effect. Returns True if successful, False otherwise."""
        pass

    def can_apply(self, context: EffectContext) -> bool:
        """Check if the effect can be applied in current context."""
        return True


class InstantEffect(Effect):
    """Base class for effects that apply immediately."""

    pass


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
            context.game_screen.message_log.append(
                f"You feel better! (+{actual_heal} HP)"
            )
            return True
        else:
            context.game_screen.message_log.append("You are already at full health.")
            return False


class TeleportEffect(InstantEffect):
    """Teleports the player to a random location."""

    def __init__(self) -> None:
        super().__init__(
            name="Teleport", description="Instantly moves you to a random location"
        )

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        dungeon = context.dungeon

        # Find a random walkable tile
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(0, dungeon.width - 1)
            y = random.randint(0, dungeon.height - 1)

            if dungeon.tiles[y][x].walkable and not dungeon.get_blocking_entity_at(
                x, y
            ):
                old_x, old_y = player.x, player.y
                player.x, player.y = x, y

                context.game_screen.message_log.append(
                    f"You teleport from ({old_x}, {old_y}) to ({x}, {y})!"
                )
                return True

        context.game_screen.message_log.append("The teleportation fails!")
        return False


class MagicMappingEffect(InstantEffect):
    """Reveals the entire dungeon map."""

    def __init__(self) -> None:
        super().__init__(
            name="Magic Mapping", description="Reveals the entire dungeon layout"
        )

    def apply(self, context: EffectContext) -> bool:
        dungeon = context.dungeon

        # Reveal all tiles
        for y in range(dungeon.height):
            for x in range(dungeon.width):
                dungeon.explored[y][x] = True

        context.game_screen.message_log.append(
            "The dungeon layout is revealed to your mind!"
        )
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

        # Mark all items as identified (if we add identification system later)
        for item in player.inventory.items:
            if hasattr(item, "identified") and not item.identified:
                item.identified = True
                unidentified_count += 1

        if unidentified_count > 0:
            context.game_screen.message_log.append(
                f"You identify {unidentified_count} item(s)!"
            )
        else:
            context.game_screen.message_log.append(
                "All your items are already known to you."
            )

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
            context.game_screen.message_log.append(
                f"You feel satisfied. (+{hunger_gained} hunger)"
            )
            return True
        else:
            context.game_screen.message_log.append("You are already full.")
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
            context.game_screen.message_log.append(
                f"You feel the curse lift from {cursed_count} item(s)!"
            )
        else:
            context.game_screen.message_log.append(
                "You don't feel any curses upon your belongings."
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
            context.game_screen.message_log.append(
                "You need to be wielding a weapon to enchant it!"
            )
            return False

        # Check enchantment limit (max +9)
        if weapon.enchantment >= 9:
            context.game_screen.message_log.append(
                "Your weapon glows briefly, but nothing happens."
            )
            return False

        weapon.enchantment += 1
        enchant_text = f"+{weapon.enchantment}" if weapon.enchantment > 0 else ""
        context.game_screen.message_log.append(
            f"Your {weapon.name} glows with magical energy! (now {enchant_text} {weapon.name})"
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
            context.game_screen.message_log.append(
                "You need to be wearing armor to enchant it!"
            )
            return False

        # Check enchantment limit (max +9)
        if armor.enchantment >= 9:
            context.game_screen.message_log.append(
                "Your armor gleams briefly, but nothing happens."
            )
            return False

        armor.enchantment += 1
        enchant_text = f"+{armor.enchantment}" if armor.enchantment > 0 else ""
        context.game_screen.message_log.append(
            f"Your {armor.name} shimmers with protective magic! (now {enchant_text} {armor.name})"
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

        context.game_screen.message_log.append(
            "A brilliant light surrounds you, expanding your vision!"
        )
        return True


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
