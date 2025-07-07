"""
セーブ・ロード管理コンポーネント。

このモジュールは、GameScreen から分離されたセーブ・ロード処理を担当します。
ゲーム状態の永続化、シリアライゼーション、デシリアライゼーションを行います。
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, Dict, List

from pyrogue.core.save_manager import SaveManager
from pyrogue.entities.items.item import Item

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class SaveLoadManager:
    """
    セーブ・ロード処理の管理クラス。

    ゲーム状態の永続化、シリアライゼーション、デシリアライゼーションを担当します。

    Attributes:
        game_screen: メインのゲームスクリーンへの参照
        save_manager: セーブファイル管理インスタンス
    """

    def __init__(self, game_screen: GameScreen) -> None:
        """
        セーブ・ロードマネージャーを初期化。

        Args:
            game_screen: メインのゲームスクリーンインスタンス
        """
        self.game_screen = game_screen
        self.save_manager = SaveManager()

    def save_game(self) -> bool:
        """
        ゲーム状態を保存。

        Returns:
            保存に成功した場合True
        """
        try:
            # 現在のフロア状態を保存
            self._save_current_floor()

            # セーブデータを作成
            save_data = self._create_save_data()

            # ファイルに保存
            success = self.save_manager.save_game(save_data)

            if success:
                self.game_screen.game_logic.add_message("Game saved successfully!")
                return True
            else:
                self.game_screen.game_logic.add_message("Failed to save game.")
                return False

        except Exception as e:
            self.game_screen.game_logic.add_message(f"Error saving game: {e}")
            return False

    def load_game(self) -> bool:
        """
        ゲーム状態を読み込み。

        Returns:
            読み込みに成功した場合True
        """
        try:
            # セーブデータを読み込み
            save_data = self.save_manager.load_game()

            if save_data is None:
                self.game_screen.game_logic.add_message("No save file found.")
                return False

            # ゲーム状態を復元
            success = self._restore_game_state(save_data)

            if success:
                # FOVを更新
                self.game_screen.fov_manager.update_fov()
                self.game_screen.game_logic.add_message("Game loaded successfully!")
                return True
            else:
                self.game_screen.game_logic.add_message("Failed to load game.")
                return False

        except Exception as e:
            self.game_screen.game_logic.add_message(f"Error loading game: {e}")
            return False

    def _save_current_floor(self) -> None:
        """
        現在のフロア状態を保存。
        """
        current_floor = self.game_screen.game_logic.dungeon_manager.current_floor
        floor_data = self.game_screen.game_logic.get_current_floor_data()

        if floor_data:
            floor_save_data = self._serialize_floor_data(floor_data)
            self.game_screen.game_logic.dungeon_manager.floor_data[current_floor] = floor_save_data

    def _create_save_data(self) -> Dict[str, Any]:
        """
        セーブデータを作成。

        Returns:
            セーブデータ辞書
        """
        player = self.game_screen.player
        dungeon_manager = self.game_screen.game_logic.dungeon_manager

        save_data = {
            "player": self._serialize_player(player),
            "inventory": self._serialize_inventory(self.game_screen.game_logic.inventory),
            "current_floor": dungeon_manager.current_floor,
            "floor_data": dungeon_manager.floor_data,
            "message_log": self.game_screen.game_logic.message_log,
            "has_amulet": getattr(player, 'has_amulet', False),
            "version": "1.0"
        }

        return save_data

    def _restore_game_state(self, save_data: Dict[str, Any]) -> bool:
        """
        セーブデータからゲーム状態を復元。

        Args:
            save_data: セーブデータ辞書

        Returns:
            復元に成功した場合True
        """
        try:
            # プレイヤー状態の復元
            player_data = save_data["player"]
            self._deserialize_player(player_data)

            # インベントリの復元
            inventory_data = save_data["inventory"]
            self._deserialize_inventory(inventory_data)

            # ダンジョン状態の復元
            dungeon_manager = self.game_screen.game_logic.dungeon_manager
            dungeon_manager.current_floor = save_data["current_floor"]
            dungeon_manager.floor_data = save_data["floor_data"]

            # メッセージログの復元
            self.game_screen.game_logic.message_log = save_data.get("message_log", [])

            # アミュレット状態の復元
            if "has_amulet" in save_data:
                self.game_screen.player.has_amulet = save_data["has_amulet"]

            # 現在のフロアを読み込み
            self._load_current_floor()

            return True

        except Exception as e:
            print(f"Error restoring game state: {e}")
            return False

    def _serialize_player(self, player) -> Dict[str, Any]:
        """
        プレイヤーオブジェクトをシリアライズ。

        Args:
            player: プレイヤーオブジェクト

        Returns:
            シリアライズされたプレイヤーデータ
        """
        return {
            "x": player.x,
            "y": player.y,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "level": player.level,
            "exp": player.exp,
            "gold": player.gold,
            "attack": player.attack,
            "defense": player.defense,
            "hunger": getattr(player, 'hunger', 100),
            "mp": getattr(player, 'mp', 0),
            "max_mp": getattr(player, 'max_mp', 0),
            "has_amulet": getattr(player, 'has_amulet', False),
        }

    def _deserialize_player(self, player_data: Dict[str, Any]) -> None:
        """
        プレイヤーデータをデシリアライズ。

        Args:
            player_data: シリアライズされたプレイヤーデータ
        """
        player = self.game_screen.player

        player.x = player_data["x"]
        player.y = player_data["y"]
        player.hp = player_data["hp"]
        player.max_hp = player_data["max_hp"]
        player.level = player_data["level"]
        player.exp = player_data["exp"]
        player.gold = player_data["gold"]
        player.attack = player_data["attack"]
        player.defense = player_data["defense"]

        # 後から追加された属性のチェック
        if "hunger" in player_data:
            player.hunger = player_data["hunger"]
        if "mp" in player_data:
            player.mp = player_data["mp"]
        if "max_mp" in player_data:
            player.max_mp = player_data["max_mp"]
        if "has_amulet" in player_data:
            player.has_amulet = player_data["has_amulet"]

    def _serialize_inventory(self, inventory) -> Dict[str, Any]:
        """
        インベントリをシリアライズ。

        Args:
            inventory: インベントリオブジェクト

        Returns:
            シリアライズされたインベントリデータ
        """
        return {
            "items": [self._serialize_item(item) for item in inventory.items],
            "equipped": {
                "weapon": self._serialize_item(inventory.equipped["weapon"]) if inventory.equipped["weapon"] else None,
                "armor": self._serialize_item(inventory.equipped["armor"]) if inventory.equipped["armor"] else None,
                "ring_left": self._serialize_item(inventory.equipped["ring_left"]) if inventory.equipped["ring_left"] else None,
                "ring_right": self._serialize_item(inventory.equipped["ring_right"]) if inventory.equipped["ring_right"] else None,
            }
        }

    def _deserialize_inventory(self, inventory_data: Dict[str, Any]) -> None:
        """
        インベントリデータをデシリアライズ。

        Args:
            inventory_data: シリアライズされたインベントリデータ
        """
        inventory = self.game_screen.game_logic.inventory

        # アイテムリストの復元
        inventory.items = [self._deserialize_item(item_data) for item_data in inventory_data["items"]]

        # 装備品の復元
        equipped_data = inventory_data["equipped"]
        inventory.equipped = {
            "weapon": self._deserialize_item(equipped_data["weapon"]) if equipped_data["weapon"] else None,
            "armor": self._deserialize_item(equipped_data["armor"]) if equipped_data["armor"] else None,
            "ring_left": self._deserialize_item(equipped_data["ring_left"]) if equipped_data["ring_left"] else None,
            "ring_right": self._deserialize_item(equipped_data["ring_right"]) if equipped_data["ring_right"] else None,
        }

    def _serialize_item(self, item: Item) -> Dict[str, Any]:
        """
        アイテムをシリアライズ。

        Args:
            item: アイテムオブジェクト

        Returns:
            シリアライズされたアイテムデータ
        """
        return {
            "item_type": item.item_type,
            "name": item.name,
            "x": getattr(item, 'x', 0),
            "y": getattr(item, 'y', 0),
            "quantity": getattr(item, 'quantity', 1),
            "enchantment": getattr(item, 'enchantment', 0),
            "cursed": getattr(item, 'cursed', False),
        }

    def _deserialize_item(self, item_data: Dict[str, Any]) -> Item:
        """
        アイテムデータをデシリアライズ。

        Args:
            item_data: シリアライズされたアイテムデータ

        Returns:
            復元されたアイテムオブジェクト
        """
        # 簡略化されたアイテム復元（基本的なItemクラスとして作成）
        item = Item(item_data["name"])

        item.item_type = item_data.get("item_type", "MISC")
        item.x = item_data.get("x", 0)
        item.y = item_data.get("y", 0)

        # 後から追加された属性のチェック
        if "quantity" in item_data:
            item.quantity = item_data["quantity"]
        if "enchantment" in item_data:
            item.enchantment = item_data["enchantment"]
        if "cursed" in item_data:
            item.cursed = item_data["cursed"]

        return item

    def _serialize_floor_data(self, floor_data) -> Dict[str, Any]:
        """
        フロアデータをシリアライズ。

        Args:
            floor_data: フロアデータオブジェクト

        Returns:
            シリアライズされたフロアデータ
        """
        return {
            "tiles": floor_data.tiles.tolist(),
            "monsters": [self._serialize_monster(monster) for monster in floor_data.monster_spawner.monsters],
            "items": [self._serialize_item(item) for item in floor_data.item_spawner.items],
            "explored": floor_data.explored.tolist(),
            "traps": [self._serialize_trap(trap) for trap in getattr(floor_data, 'trap_manager', {}).get('traps', [])]
        }

    def _serialize_monster(self, monster) -> Dict[str, Any]:
        """
        モンスターをシリアライズ。

        Args:
            monster: モンスターオブジェクト

        Returns:
            シリアライズされたモンスターデータ
        """
        return {
            "monster_type": monster.monster_type,
            "x": monster.x,
            "y": monster.y,
            "hp": monster.hp,
            "max_hp": monster.max_hp,
        }

    def _serialize_trap(self, trap) -> Dict[str, Any]:
        """
        トラップをシリアライズ。

        Args:
            trap: トラップオブジェクト

        Returns:
            シリアライズされたトラップデータ
        """
        return {
            "trap_type": trap.trap_type,
            "x": trap.x,
            "y": trap.y,
            "hidden": trap.hidden,
        }

    def _load_current_floor(self) -> None:
        """
        現在のフロアをロード。
        """
        current_floor = self.game_screen.game_logic.dungeon_manager.current_floor
        floor_data = self.game_screen.game_logic.dungeon_manager.get_floor_data(current_floor)

        if floor_data:
            # 既存のフロアデータを復元
            self._deserialize_floor_data(floor_data)
        else:
            # フロアデータが存在しない場合は新規生成
            self.game_screen.game_logic.dungeon_manager.generate_floor(current_floor)

    def _deserialize_floor_data(self, floor_data: Dict[str, Any]) -> None:
        """
        フロアデータをデシリアライズ。

        Args:
            floor_data: シリアライズされたフロアデータ
        """
        # 実装は複雑になるため、基本的な復元のみ
        # 詳細な復元はGameLogic側で実装
        pass

    def has_save_file(self) -> bool:
        """
        セーブファイルが存在するかチェック。

        Returns:
            セーブファイルが存在する場合True
        """
        return self.save_manager.has_save_file()

    def delete_save_file(self) -> bool:
        """
        セーブファイルを削除。

        Returns:
            削除に成功した場合True
        """
        return self.save_manager.delete_save_file()
