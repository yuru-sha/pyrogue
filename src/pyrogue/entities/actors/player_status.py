"""
Player status formatting utilities.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.entities.actors.player import Player


class PlayerStatusFormatter:
    """Handles formatting of player status information."""
    
    @staticmethod
    def format_status(player: "Player") -> str:
        """
        Format player status for display.
        
        Args:
            player: Player instance
            
        Returns:
            Formatted status string
        """
        weapon = player.inventory.get_equipped_item_name("weapon")
        armor = player.inventory.get_equipped_item_name("armor")
        ring_l = player.inventory.get_equipped_item_name("ring_left")
        ring_r = player.inventory.get_equipped_item_name("ring_right")

        return (
            f"Lv:{player.level} HP:{player.hp}/{player.max_hp} "
            f"Atk:{player.get_attack()} Def:{player.get_defense()} "
            f"Hunger:{player.hunger}% Exp:{player.exp} Gold:{player.gold}\n"
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
            'level': player.level,
            'hp': player.hp,
            'max_hp': player.max_hp,
            'attack': player.get_attack(),
            'defense': player.get_defense(),
            'exp': player.exp,
            'gold': player.gold,
            'hunger': player.hunger,
        }