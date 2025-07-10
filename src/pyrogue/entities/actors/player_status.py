"""
Player status formatting utilities.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.entities.actors.player import Player


class PlayerStatusFormatter:
    """プレイヤーステータス情報のフォーマットを処理。"""

    @staticmethod
    def format_status(player: "Player") -> str:
        """
        表示用のプレイヤーステータスをフォーマット。

        Args:
            player: プレイヤーインスタンス

        Returns:
            フォーマットされたステータス文字列

        """
        weapon = player.inventory.get_equipped_item_name("weapon")
        armor = player.inventory.get_equipped_item_name("armor")
        ring_l = player.inventory.get_equipped_item_name("ring_left")
        ring_r = player.inventory.get_equipped_item_name("ring_right")

        # 状態異常の表示
        status_effects_text = player.status_effects.get_effect_summary()
        status_line = f" [{status_effects_text}]" if status_effects_text else ""

        # 飢餓状態の表示
        hunger_level = player.get_hunger_level()
        hunger_display = f"{hunger_level}({player.hunger}%)"

        return (
            f"Lv:{player.level} HP:{player.hp}/{player.max_hp} MP:{player.mp}/{player.max_mp} "
            f"Atk:{player.get_attack()} Def:{player.get_defense()} "
            f"Hunger:{hunger_display} Exp:{player.exp} Gold:{player.gold}{status_line}\n"
            f"Weap:{weapon} Armor:{armor} Ring(L):{ring_l} Ring(R):{ring_r}"
        )

    @staticmethod
    def format_stats_dict(player: "Player") -> dict:
        """
        Format player stats as dictionary for game over/victory screens.

        Args:
            player: Player instance

        Returns:
            Dictionary containing player stats

        """
        return {
            "level": player.level,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.get_attack(),
            "defense": player.get_defense(),
            "exp": player.exp,
            "gold": player.gold,
            "hunger": player.hunger,
            "score": player.calculate_score(),
            "monsters_killed": player.monsters_killed,
            "deepest_floor": player.deepest_floor,
            "turns_played": player.turns_played,
            "items_used": player.items_used,
        }
