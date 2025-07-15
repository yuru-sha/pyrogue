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
    if hasattr(context, "add_message") or (
        hasattr(context, "game_screen") and hasattr(context.game_screen, "message_log")
    ):
        context.add_message(message)


def _get_floor_data_safe(context):
    """コンテキストから安全にフロアデータを取得するヘルパー関数。"""
    if hasattr(context, "dungeon_manager"):
        return context.dungeon_manager.get_current_floor_data()
    if hasattr(context, "dungeon"):
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

    def add_message(self, message: str, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """Add a message to the game log."""
        ...


class Effect(ABC):
    """Abstract base class for all item effects."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def apply(self, context: EffectContext, **kwargs) -> bool:
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
        super().__init__(name="Teleport", description="Instantly moves you to a random location")

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

            if floor_data.tiles[y][x].walkable and not floor_data.monster_spawner.get_monster_at(x, y):
                old_x, old_y = player.x, player.y
                player.x, player.y = x, y

                _add_message_safe(context, f"You teleport from ({old_x}, {old_y}) to ({x}, {y})!")
                return True

        _add_message_safe(context, "The teleportation fails!")
        return False


class MagicMappingEffect(InstantEffect):
    """Reveals the entire dungeon map."""

    def __init__(self) -> None:
        super().__init__(name="Magic Mapping", description="Reveals the entire dungeon layout")

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
        super().__init__(name="Identify", description="Reveals the true nature of your items")

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        unidentified_count = 0

        # 新しい識別システムを使用
        for item in player.inventory.items:
            if hasattr(item, "item_type") and hasattr(item, "name"):
                # 未識別のアイテムのみ処理
                if not player.identification.is_identified(item.name, item.item_type):
                    was_identified = player.identification.identify_item(item.name, item.item_type)
                    if was_identified:
                        unidentified_count += 1
                        # 識別メッセージを追加
                        msg = player.identification.get_identification_message(item.name, item.item_type)
                        _add_message_safe(context, msg)

        if unidentified_count > 0:
            _add_message_safe(context, f"You identify {unidentified_count} item(s)!")
        else:
            _add_message_safe(context, "All your items are already known to you.")

        return True


class NutritionEffect(InstantEffect):
    """Restores hunger/nutrition."""

    def __init__(self, nutrition_value: int) -> None:
        super().__init__(name="Nutrition", description=f"Restores {nutrition_value} hunger")
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
        super().__init__(name="Remove Curse", description="Removes the curse from all your items")

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
            _add_message_safe(context, f"You feel the curse lift from {cursed_count} item(s)!")
        else:
            _add_message_safe(context, "You don't feel any curses upon your belongings.")

        return True


class EnchantWeaponEffect(InstantEffect):
    """Enchants the currently equipped weapon."""

    def __init__(self) -> None:
        super().__init__(name="Enchant Weapon", description="Magically enhances your weapon")

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        weapon = player.inventory.get_equipped_weapon()

        if not weapon:
            _add_message_safe(context, "You need to be wielding a weapon to enchant it!")
            return False

        # Check enchantment limit (max +9)
        if weapon.enchantment >= 9:
            _add_message_safe(context, "Your weapon glows briefly, but nothing happens.")
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
        super().__init__(name="Enchant Armor", description="Magically enhances your armor")

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        armor = player.inventory.get_equipped_armor()

        if not armor:
            _add_message_safe(context, "You need to be wearing armor to enchant it!")
            return False

        # Check enchantment limit (max +9)
        if armor.enchantment >= 9:
            _add_message_safe(context, "Your armor gleams briefly, but nothing happens.")
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
        super().__init__(name="Light", description=f"Illuminates a wide area for {duration} turns")
        self.duration = duration
        self.radius = radius

    def apply(self, context: EffectContext) -> bool:
        player = context.player
        player.apply_light_effect(self.duration, self.radius)

        _add_message_safe(context, "A brilliant light surrounds you, expanding your vision!")
        return True


class StatusEffectApplication(InstantEffect):
    """Applies a status effect to the player."""

    def __init__(self, status_effect_class, name: str, description: str, **kwargs) -> None:
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


# Wand-specific effects
class WandEffect(Effect):
    """Base class for wand effects that require direction."""

    def __init__(self, name: str, description: str, damage_range: tuple[int, int] = (0, 0)):
        super().__init__(name, description)
        self.damage_range = damage_range

    def get_damage(self) -> int:
        """Get random damage value within range."""
        if self.damage_range[0] == self.damage_range[1]:
            return self.damage_range[0]
        return random.randint(self.damage_range[0], self.damage_range[1])

    def find_target_in_direction(self, context: EffectContext, direction: tuple[int, int], max_range: int = 10):
        """Find the first monster in the given direction."""
        player = context.player
        start_x, start_y = player.x, player.y
        dx, dy = direction

        current_floor = _get_floor_data_safe(context)
        if not current_floor:
            return None, None, None

        for distance in range(1, max_range + 1):
            target_x = start_x + dx * distance
            target_y = start_y + dy * distance

            # Check bounds
            if target_x < 0 or target_x >= 80 or target_y < 0 or target_y >= 45:
                break

            # Check for wall collision
            if not current_floor.tiles[target_y][target_x].walkable:
                break

            # Check for monster
            monster = current_floor.monster_spawner.get_monster_at(target_x, target_y)
            if monster:
                return monster, target_x, target_y

        return None, None, None


class MagicMissileWandEffect(WandEffect):
    """Magic missile wand effect - never misses."""

    def __init__(self, damage_range: tuple[int, int] = (3, 8)):
        super().__init__("Magic Missile", "Shoots a magical projectile that always hits", damage_range)

    def apply(self, context: EffectContext, **kwargs) -> bool:
        direction = kwargs.get("direction", (0, 0))
        if direction == (0, 0):
            _add_message_safe(context, "You need to choose a direction!")
            return False

        monster, target_x, target_y = self.find_target_in_direction(context, direction)

        if monster:
            damage = self.get_damage()
            monster.hp = max(0, monster.hp - damage)
            _add_message_safe(context, f"Your magic missile hits the {monster.name} for {damage} damage!")

            # Check if monster dies
            if monster.hp <= 0:
                _add_message_safe(context, f"The {monster.name} dies!")
                context.player.gain_exp(monster.exp_value)
                # Remove monster from floor
                current_floor = _get_floor_data_safe(context)
                if current_floor and monster in current_floor.monster_spawner.monsters:
                    current_floor.monster_spawner.monsters.remove(monster)
        else:
            _add_message_safe(context, "Your magic missile dissipates harmlessly.")

        return True


class LightningWandEffect(WandEffect):
    """Lightning wand effect - hits in a straight line."""

    def __init__(self, damage_range: tuple[int, int] = (6, 15)):
        super().__init__("Lightning", "Shoots a bolt of lightning", damage_range)

    def apply(self, context: EffectContext, **kwargs) -> bool:
        direction = kwargs.get("direction", (0, 0))
        if direction == (0, 0):
            _add_message_safe(context, "You need to choose a direction!")
            return False

        monster, target_x, target_y = self.find_target_in_direction(context, direction)

        if monster:
            damage = self.get_damage()
            monster.hp = max(0, monster.hp - damage)
            _add_message_safe(context, f"Lightning strikes the {monster.name} for {damage} damage!")

            # Check if monster dies
            if monster.hp <= 0:
                _add_message_safe(context, f"The {monster.name} is electrocuted!")
                context.player.gain_exp(monster.exp_value)
                # Remove monster from floor
                current_floor = _get_floor_data_safe(context)
                if current_floor and monster in current_floor.monster_spawner.monsters:
                    current_floor.monster_spawner.monsters.remove(monster)
        else:
            _add_message_safe(context, "Lightning crackles harmlessly through the air.")

        return True


class LightWandEffect(WandEffect):
    """Light wand effect - illuminates the area."""

    def __init__(self):
        super().__init__("Light", "Creates a bright light", (0, 0))

    def apply(self, context: EffectContext, **kwargs) -> bool:
        # Light up the area around the player
        player = context.player
        current_floor = _get_floor_data_safe(context)

        if current_floor:
            # Light up a 5x5 area around the player
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    x, y = player.x + dx, player.y + dy
                    if 0 <= x < 80 and 0 <= y < 45:
                        current_floor.explored[y][x] = True

        _add_message_safe(context, "The area is lit up by magical light!")
        return True


class NothingWandEffect(WandEffect):
    """Nothing wand effect - does nothing."""

    def __init__(self):
        super().__init__("Nothing", "Does absolutely nothing", (0, 0))

    def apply(self, context: EffectContext, **kwargs) -> bool:
        _add_message_safe(context, "Nothing happens.")
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
POISON_POTION = PoisonPotionEffect()
PARALYSIS_POTION = ParalysisPotionEffect()
CONFUSION_POTION = ConfusionPotionEffect()
HALLUCINATION_POTION = HallucinationPotionEffect()

# Pre-defined wand effects
MAGIC_MISSILE_WAND = MagicMissileWandEffect()
LIGHTNING_WAND = LightningWandEffect()
LIGHT_WAND = LightWandEffect()
NOTHING_WAND = NothingWandEffect()
