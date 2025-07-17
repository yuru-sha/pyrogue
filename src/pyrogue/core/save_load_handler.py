"""
セーブ・ロードコマンドハンドラーモジュール。

セーブ・ロード機能に関するコマンド処理を専門に担当します。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyrogue.core.command_handler import CommandResult

if TYPE_CHECKING:
    from pyrogue.core.command_handler import CommandContext


class SaveLoadHandler:
    """セーブ・ロードコマンド専用のハンドラー。"""

    def __init__(self, context: CommandContext):
        self.context = context

    def handle_save(self, args: list[str]) -> CommandResult:
        """
        セーブコマンドの処理。

        Args:
        ----
            args: コマンド引数（現在未使用）

        Returns:
        -------
            CommandResult: セーブ実行結果

        """
        # SaveManagerを使用してセーブを実行
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()

        # 現在のゲーム状態を取得
        try:
            game_data = self._create_save_data()
            success = save_manager.save_game_state(game_data)

            if success:
                self.context.add_message("Game saved successfully!")
                return CommandResult(True)
            self.context.add_message("Failed to save game.")
            return CommandResult(False)

        except Exception as e:
            self.context.add_message(f"Error saving game: {e}")
            return CommandResult(False)

    def handle_load(self, args: list[str]) -> CommandResult:
        """
        ロードコマンドの処理。

        Args:
        ----
            args: コマンド引数（現在未使用）

        Returns:
        -------
            CommandResult: ロード実行結果

        """
        # SaveManagerを使用してロードを実行
        from pyrogue.core.save_manager import SaveManager

        save_manager = SaveManager()

        try:
            save_data = save_manager.load_game_state()

            if save_data is None:
                self.context.add_message("No save file found.")
                return CommandResult(False)

            # セーブデータの復元
            success = self._restore_save_data(save_data)

            if success:
                self.context.add_message("Game loaded successfully!")
                return CommandResult(True)
            self.context.add_message("Failed to load game.")
            return CommandResult(False)

        except Exception as e:
            self.context.add_message(f"Error loading game: {e}")
            return CommandResult(False)

    def _create_save_data(self) -> dict[str, Any]:
        """
        セーブデータを作成（GUIモードと同じ完全保存）。

        Returns
        -------
            dict: セーブデータ辞書

        """
        player = self.context.player
        dungeon_manager = self.context.game_logic.dungeon_manager

        # GUIモードと同じ完全なセーブデータを作成
        save_data = {
            "player": self._serialize_player(player),
            "inventory": self._serialize_inventory(self.context.game_logic.inventory),
            "current_floor": dungeon_manager.current_floor,
            "floor_data": self._serialize_all_floors(dungeon_manager.floors),
            "message_log": self.context.game_logic.message_log,
            "has_amulet": getattr(player, "has_amulet", False),
            "version": "1.0",
        }

        return save_data

    def _restore_save_data(self, save_data: dict[str, Any]) -> bool:
        """
        セーブデータからゲーム状態を復元（GUIモードと同じ完全復元）。

        Args:
        ----
            save_data: セーブデータ辞書

        Returns:
        -------
            bool: 復元に成功した場合True

        """
        try:
            # プレイヤー状態の復元
            player_data = save_data.get("player", {})
            if player_data:
                self._deserialize_player(player_data)

            # インベントリの復元
            inventory_data = save_data.get("inventory", {})
            if inventory_data:
                self._deserialize_inventory(inventory_data)

            # ダンジョン状態の復元
            dungeon_manager = self.context.game_logic.dungeon_manager
            dungeon_manager.current_floor = save_data.get("current_floor", 1)

            # フロアデータを正しく復元
            floor_data = save_data.get("floor_data", {})
            if floor_data:
                self._restore_floor_data(floor_data)

            # メッセージログの復元
            message_log = save_data.get("message_log", [])
            if hasattr(self.context.game_logic, "message_log"):
                # GameLogicのmessage_logを更新
                self.context.game_logic.message_log.clear()
                self.context.game_logic.message_log.extend(message_log)

                # GameContextのmessage_logも同じリストを参照するよう更新
                self.context.message_log = self.context.game_logic.message_log

            # アミュレット状態の復元
            if "has_amulet" in save_data:
                self.context.player.has_amulet = save_data["has_amulet"]

            # 現在のフロアを読み込み
            self._load_current_floor()

            return True

        except Exception as e:
            print(f"Error restoring save data: {e}")
            return False

    def _deserialize_player(self, player_data: dict[str, Any]) -> None:
        """
        プレイヤーデータをデシリアライズ。
        """
        player = self.context.player

        player.x = player_data.get("x", player.x)
        player.y = player_data.get("y", player.y)
        player.hp = player_data.get("hp", player.hp)
        player.max_hp = player_data.get("max_hp", player.max_hp)
        player.level = player_data.get("level", player.level)
        player.exp = player_data.get("exp", player.exp)
        player.gold = player_data.get("gold", player.gold)
        player.attack = player_data.get("attack", player.attack)
        player.defense = player_data.get("defense", player.defense)

        # オプション属性の復元
        if "hunger" in player_data:
            player.hunger = player_data["hunger"]
        # if "mp" in player_data:
        #     player.mp = player_data["mp"]
        # if "max_mp" in player_data:
        #     player.max_mp = player_data["max_mp"]
        if "has_amulet" in player_data:
            player.has_amulet = player_data["has_amulet"]

    def _deserialize_inventory(self, inventory_data: dict[str, Any]) -> None:
        """
        インベントリデータをデシリアライズ。
        軽量な状態データから完全なアイテムオブジェクトを復元する。
        """
        inventory = self.context.game_logic.inventory

        # アイテムリストの復元
        items_data = inventory_data.get("items", [])
        inventory.items = [self._deserialize_item(item_data) for item_data in items_data]

        # 装備品の復元（インデックスベース）
        equipped_data = inventory_data.get("equipped", {})
        inventory.equipped = {
            "weapon": None,
            "armor": None,
            "ring_left": None,
            "ring_right": None,
        }

        # インデックスから実際のアイテムオブジェクトに変換
        for slot, index in equipped_data.items():
            if index is not None and 0 <= index < len(inventory.items):
                inventory.equipped[slot] = inventory.items[index]

    def _serialize_player(self, player) -> dict[str, Any]:
        """
        プレイヤーオブジェクトをシリアライズ。
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
            "hunger": getattr(player, "hunger", 100),
            # "mp": getattr(player, "mp", 0),
            # "max_mp": getattr(player, "max_mp", 0),
            "has_amulet": getattr(player, "has_amulet", False),
        }

    def _serialize_inventory(self, inventory) -> dict[str, Any]:
        """
        インベントリをシリアライズ。
        """
        if inventory is None:
            return {"items": [], "equipped": {"weapon": None, "armor": None, "ring_left": None, "ring_right": None}}

        # アイテムリストのシリアライズ
        items_data = [self._serialize_item(item) for item in inventory.items]

        # 装備状態をインデックスベースで保存
        equipped_indices = {}
        for slot, item in inventory.equipped.items():
            if item is not None:
                # インベントリ内でのインデックスを検索
                try:
                    index = inventory.items.index(item)
                    equipped_indices[slot] = index
                except ValueError:
                    # インベントリに見つからない場合はNone
                    equipped_indices[slot] = None
            else:
                equipped_indices[slot] = None

        return {
            "items": items_data,
            "equipped": equipped_indices,
        }

    def _serialize_item(self, item) -> dict[str, Any]:
        """
        アイテムを軽量な状態データとしてシリアライズ。
        IDベース＋状態データで実装詳細に依存しない形式。
        """
        from pyrogue.entities.items.item_factory import ItemFactory

        # アイテムIDを取得（オブジェクトから直接、または名前から）
        item_id = getattr(item, "item_id", None)
        if item_id is None or item_id == 0:
            # IDが設定されていない場合は名前から取得
            item_id = ItemFactory.get_id_by_name(item.name)

        data = {
            "item_id": item_id,  # 主キー：アイテムID
            "name": item.name,  # 後方互換性用：アイテム名
            "x": getattr(item, "x", 0),  # アイテムの位置情報
            "y": getattr(item, "y", 0),  # アイテムの位置情報
            "char": getattr(item, "char", "?"),  # 表示文字
            "color": getattr(item, "color", (255, 255, 255)),  # 表示色
            "count": getattr(item, "stack_count", 1),
            "identified": getattr(item, "identified", True),
            "blessed": getattr(item, "blessed", False),
            "cursed": getattr(item, "cursed", False),
            "enchantment": getattr(item, "enchantment", 0),
        }

        # アイテム固有の状態属性
        if hasattr(item, "charges"):
            data["charges"] = item.charges
        if hasattr(item, "amount"):  # Gold用
            data["amount"] = item.amount
        if hasattr(item, "bonus"):  # Ring用
            data["bonus"] = item.bonus
        if hasattr(item, "effect") and hasattr(item, "item_type") and item.item_type == "RING":
            # Ringの効果名のみ保存（文字列として）
            data["effect_name"] = (
                getattr(item.effect, "name", item.effect) if isinstance(item.effect, str) else item.effect
            )

        return data

    def _deserialize_item(self, item_data: dict[str, Any]):
        """
        IDベースでアイテムオブジェクトを復元。名前変更に対応し、後方互換性も維持。
        """
        from pyrogue.entities.items.item_factory import ItemFactory
        from pyrogue.entities.items.item_spawner import ItemSpawner

        item_id = item_data.get("item_id")
        name = item_data.get("name", "Unknown Item")

        # IDベース復元を優先
        if item_id is not None:
            try:
                item = ItemFactory.create_by_id(item_id, 0, 0)
            except ValueError:
                # 不明なIDの場合は名前ベースにフォールバック
                spawner = ItemSpawner(floor=1)
                item = self._create_item_by_name(spawner, name)
        else:
            # IDがない場合（旧セーブデータ）は名前ベース
            spawner = ItemSpawner(floor=1)
            item = self._create_item_by_name(spawner, name)

        if item is None:
            # フォールバック: 基本的なアイテムを作成
            from pyrogue.entities.items.item import Item

            item = Item(x=0, y=0, name=name, char="?", color=(255, 255, 255), item_type="MISC", cursed=False)

        # 保存された状態を適用
        self._apply_item_state(item, item_data)

        # 位置情報を復元
        if "x" in item_data and "y" in item_data:
            item.x = item_data["x"]
            item.y = item_data["y"]

        # 表示情報を復元
        if "char" in item_data:
            item.char = item_data["char"]
        if "color" in item_data:
            item.color = item_data["color"]

        return item

    def _create_item_by_name(self, spawner, name: str):
        """
        アイテム名から適切なアイテムオブジェクトを直接生成。
        ItemSpawnerは使用せず、直接アイテムクラスを使用する。
        """
        from pyrogue.entities.items.amulet import AmuletOfYendor
        from pyrogue.entities.items.effects import (
            ConfusionPotionEffect,
            EnchantArmorEffect,
            EnchantWeaponEffect,
            HallucinationPotionEffect,
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

        try:
            # 食料
            if name == "Food Ration":
                return Food(0, 0, "Food Ration", NutritionEffect(25))

            # ポーション
            if name == "Potion of Healing":
                return Potion(0, 0, "Potion of Healing", HealingEffect(25))
            if name == "Potion of Extra Healing":
                return Potion(0, 0, "Potion of Extra Healing", HealingEffect(50))
            if name == "Potion of Poison":
                return Potion(0, 0, "Potion of Poison", PoisonPotionEffect())
            if name == "Potion of Paralysis":
                return Potion(0, 0, "Potion of Paralysis", ParalysisPotionEffect())
            if name == "Potion of Confusion":
                return Potion(0, 0, "Potion of Confusion", ConfusionPotionEffect())
            if name == "Potion of Hallucination":
                return Potion(0, 0, "Potion of Hallucination", HallucinationPotionEffect())

            # 巻物
            if name == "Scroll of Light":
                return Scroll(0, 0, "Scroll of Light", LightEffect())
            if name == "Scroll of Teleportation":
                return Scroll(0, 0, "Scroll of Teleportation", TeleportEffect())
            if name == "Scroll of Magic Mapping":
                return Scroll(0, 0, "Scroll of Magic Mapping", MagicMappingEffect())
            if name == "Scroll of Identify":
                return Scroll(0, 0, "Scroll of Identify", IdentifyEffect())
            if name == "Scroll of Remove Curse":
                return Scroll(0, 0, "Scroll of Remove Curse", RemoveCurseEffect())
            if name == "Scroll of Enchant Weapon":
                return Scroll(0, 0, "Scroll of Enchant Weapon", EnchantWeaponEffect())
            if name == "Scroll of Enchant Armor":
                return Scroll(0, 0, "Scroll of Enchant Armor", EnchantArmorEffect())

            # 杖
            if name == "Wand of Magic Missile":
                return Wand(0, 0, "Wand of Magic Missile", MagicMissileWandEffect(), 3)
            if name == "Wand of Lightning":
                return Wand(0, 0, "Wand of Lightning", LightningWandEffect(), 3)
            if name == "Wand of Light":
                return Wand(0, 0, "Wand of Light", LightWandEffect(), 3)
            if name == "Wand of Nothing":
                return Wand(0, 0, "Wand of Nothing", NothingWandEffect(), 3)

            # 武器
            if name == "Dagger":
                return Weapon(0, 0, "Dagger", 2)
            if name == "Short Sword":
                return Weapon(0, 0, "Short Sword", 3)
            if name == "Long Sword":
                return Weapon(0, 0, "Long Sword", 4)
            if name == "Mace":
                return Weapon(0, 0, "Mace", 3)

            # 防具
            if name == "Leather Armor":
                return Armor(0, 0, "Leather Armor", 2)
            if name == "Chain Mail":
                return Armor(0, 0, "Chain Mail", 3)
            if name == "Plate Mail":
                return Armor(0, 0, "Plate Mail", 4)

            # 指輪
            if name == "Ring of Protection":
                return Ring(0, 0, "Ring of Protection", "protection", 1)
            if name == "Ring of Add Strength":
                return Ring(0, 0, "Ring of Add Strength", "strength", 1)
            if name == "Ring of Sustain Strength":
                return Ring(0, 0, "Ring of Sustain Strength", "sustain", 1)
            if name == "Ring of Searching":
                return Ring(0, 0, "Ring of Searching", "search", 1)
            if name == "Ring of See Invisible":
                return Ring(0, 0, "Ring of See Invisible", "see_invisible", 1)
            if name == "Ring of Regeneration":
                return Ring(0, 0, "Ring of Regeneration", "regeneration", 1)

            # 特別なアイテム
            if name == "Gold":
                return Gold(0, 0, 1)
            if name == "Amulet of Yendor":
                return AmuletOfYendor(0, 0)

        except Exception as e:
            print(f"Warning: Failed to create item '{name}': {e}")

        return None

    def _apply_item_state(self, item, item_data: dict[str, Any]):
        """
        保存された状態データをアイテムに適用。
        """
        # 基本状態の適用
        if "count" in item_data and hasattr(item, "stack_count"):
            item.stack_count = max(1, item_data["count"])

        if "identified" in item_data and hasattr(item, "identified"):
            item.identified = item_data["identified"]

        if "blessed" in item_data and hasattr(item, "blessed"):
            item.blessed = item_data["blessed"]

        if "cursed" in item_data and hasattr(item, "cursed"):
            item.cursed = item_data["cursed"]

        if "enchantment" in item_data and hasattr(item, "enchantment"):
            item.enchantment = item_data["enchantment"]

        # アイテム固有状態の適用
        if "charges" in item_data and hasattr(item, "charges"):
            item.charges = max(0, item_data["charges"])

        if "amount" in item_data and hasattr(item, "amount"):
            item.amount = max(1, item_data["amount"])

        if "bonus" in item_data and hasattr(item, "bonus"):
            item.bonus = item_data["bonus"]

        if "effect_name" in item_data and hasattr(item, "effect"):
            # Ringの効果名を文字列として保存している場合
            item.effect = item_data["effect_name"]

    def _serialize_all_floors(self, floors: dict[int, Any]) -> dict[str, Any]:
        """
        すべてのフロアデータをシリアライズ。
        """
        serialized_floors = {}
        for floor_num, floor_data in floors.items():
            if floor_data is not None:
                serialized_floors[floor_num] = self._serialize_floor_data_object(floor_data)
        return serialized_floors

    def _serialize_floor_data_object(self, floor_data) -> dict[str, Any]:
        """
        フロアデータオブジェクトをシリアライズ。
        """
        return {
            "tiles": floor_data.tiles.tolist(),
            "monsters": [self._serialize_monster(monster) for monster in floor_data.monster_spawner.monsters],
            "items": [self._serialize_item(item) for item in floor_data.item_spawner.items],
            "explored": floor_data.explored.tolist(),
            "traps": [
                self._serialize_trap(trap) for trap in getattr(getattr(floor_data, "trap_manager", None), "traps", [])
            ],
        }

    def _restore_floor_data(self, floor_data: dict[str, Any]) -> None:
        """
        フロアデータを復元（完全実装）。
        """
        import numpy as np

        from pyrogue.entities.actors.monster_spawner import MonsterSpawner
        from pyrogue.entities.items.item_spawner import ItemSpawner
        from pyrogue.entities.traps.trap import TrapManager
        from pyrogue.map.dungeon_manager import FloorData

        dungeon_manager = self.context.game_logic.dungeon_manager

        # 既存のフロアをクリア（復元成功時のみ）
        floors_backup = dungeon_manager.floors.copy()

        # セーブされたフロアデータを復元
        if not floor_data:
            self.context.add_message("No saved floor data found - floors will be regenerated")
            return

        try:
            # 復元成功時のみ既存フロアをクリア
            dungeon_manager.floors.clear()

            for floor_num_str, saved_floor_data in floor_data.items():
                floor_num = int(floor_num_str)

                # タイルデータを復元
                tiles_list = saved_floor_data.get("tiles", [])
                if tiles_list:
                    tiles = np.array(tiles_list, dtype=object)
                else:
                    continue  # タイルデータがない場合はスキップ

                # 探索済みデータを復元
                explored_list = saved_floor_data.get("explored", [])
                if explored_list:
                    explored = np.array(explored_list, dtype=bool)
                else:
                    explored = np.zeros_like(tiles, dtype=bool)

                # MonsterSpawnerを復元
                has_amulet = getattr(self.context.player, "has_amulet", False)
                monster_spawner = MonsterSpawner(floor_num, has_amulet)
                monsters_data = saved_floor_data.get("monsters", [])
                for monster_data in monsters_data:
                    monster = self._deserialize_monster(monster_data)
                    if monster:
                        monster_spawner.monsters.append(monster)

                # ItemSpawnerを復元
                item_spawner = ItemSpawner(floor_num)
                items_data = saved_floor_data.get("items", [])
                for item_data in items_data:
                    item = self._deserialize_item(item_data)
                    if item:
                        item_spawner.items.append(item)

                # TrapManagerを復元
                trap_manager = TrapManager()
                traps_data = saved_floor_data.get("traps", [])
                for trap_data in traps_data:
                    trap = self._deserialize_trap(trap_data)
                    if trap:
                        trap_manager.traps.append(trap)

                # 階段位置を検索
                up_pos = None
                down_pos = None

                for y in range(tiles.shape[0]):
                    for x in range(tiles.shape[1]):
                        tile = tiles[y, x]
                        tile_name = tile.__class__.__name__ if hasattr(tile, "__class__") else str(tile)
                        if "StairsUp" in tile_name or "UpStairs" in tile_name:
                            up_pos = (x, y)
                        elif "StairsDown" in tile_name or "DownStairs" in tile_name:
                            down_pos = (x, y)

                # 階段が見つからない場合のデフォルト値
                if up_pos is None:
                    up_pos = (1, 1)  # デフォルト位置
                if down_pos is None:
                    down_pos = (tiles.shape[1] - 2, tiles.shape[0] - 2)  # デフォルト位置

                # FloorDataオブジェクトを作成
                restored_floor = FloorData(
                    floor_number=floor_num,
                    tiles=tiles,
                    up_pos=up_pos,
                    down_pos=down_pos,
                    monster_spawner=monster_spawner,
                    item_spawner=item_spawner,
                    trap_manager=trap_manager,
                    explored=explored,
                )

                # DungeonManagerに追加
                dungeon_manager.floors[floor_num] = restored_floor

            self.context.add_message(f"Successfully restored {len(floor_data)} floors from save data")

        except Exception as e:
            self.context.add_message(f"Error restoring floor data: {e}")
            # エラーが発生した場合はバックアップから復元
            dungeon_manager.floors = floors_backup
            self.context.add_message("Floor data restored from backup - some floors may be regenerated")

    def _load_current_floor(self) -> None:
        """
        現在のフロアをロード。
        """
        current_floor = self.context.game_logic.dungeon_manager.current_floor
        floor_data = self.context.game_logic.dungeon_manager.floors.get(current_floor)

        if floor_data:
            # 既存のフロアデータを復元
            self._deserialize_floor_data(floor_data)
        else:
            # フロアデータが存在しない場合は新規生成
            self.context.game_logic.dungeon_manager._generate_floor(current_floor, self.context.player)

    def _deserialize_floor_data(self, floor_data: dict[str, Any]) -> None:
        """
        フロアデータをデシリアライズ。
        """
        # 実装は複雑になるため、基本的な復元のみ
        # 詳細な復元はGameLogic側で実装

    def _serialize_monster(self, monster) -> dict[str, Any]:
        """
        モンスターをシリアライズ。
        """
        return {
            "name": monster.name,
            "char": monster.char,
            "x": monster.x,
            "y": monster.y,
            "hp": monster.hp,
            "max_hp": monster.max_hp,
            "attack": monster.attack,
            "defense": monster.defense,
            "level": monster.level,
            "exp_value": getattr(monster, "exp_value", 0),
            "ai_pattern": getattr(monster, "ai_pattern", "basic"),
            "color": getattr(monster, "color", (255, 255, 255)),
            "view_range": getattr(monster, "view_range", 3),
        }

    def _serialize_trap(self, trap) -> dict[str, Any]:
        """
        トラップをシリアライズ。
        """
        return {
            "trap_type": trap.trap_type,
            "x": trap.x,
            "y": trap.y,
            "hidden": trap.is_hidden,
        }

    def _deserialize_monster(self, monster_data: dict[str, Any]):
        """
        モンスターデータをデシリアライズ。
        """
        from pyrogue.entities.actors.monster import Monster

        try:
            monster = Monster(
                x=monster_data.get("x", 0),
                y=monster_data.get("y", 0),
                name=monster_data.get("name", "Unknown Monster"),
                char=monster_data.get("char", "?"),
                hp=monster_data.get("hp", 1),
                max_hp=monster_data.get("max_hp", 1),
                attack=monster_data.get("attack", 1),
                defense=monster_data.get("defense", 0),
                level=monster_data.get("level", 1),
                exp_value=monster_data.get("exp_value", 10),
                view_range=monster_data.get("view_range", 3),
                color=monster_data.get("color", (255, 255, 255)),
            )

            # AI パターンの復元
            if "ai_pattern" in monster_data:
                monster.ai_pattern = monster_data["ai_pattern"]

            return monster

        except Exception as e:
            self.context.add_message(f"Error deserializing monster: {e}")
            return None

    def _deserialize_trap(self, trap_data: dict[str, Any]):
        """
        トラップデータをデシリアライズ。
        """
        try:
            trap_type = trap_data.get("trap_type", "PitTrap")
            x = trap_data.get("x", 0)
            y = trap_data.get("y", 0)
            is_hidden = trap_data.get("hidden", True)

            # トラップタイプに応じてインスタンスを作成
            if trap_type == "PitTrap":
                from pyrogue.entities.traps.trap import PitTrap

                trap = PitTrap(x, y)
            elif trap_type == "PoisonNeedleTrap":
                from pyrogue.entities.traps.trap import PoisonNeedleTrap

                trap = PoisonNeedleTrap(x, y)
            elif trap_type == "TeleportTrap":
                from pyrogue.entities.traps.trap import TeleportTrap

                trap = TeleportTrap(x, y)
            else:
                # 不明なトラップタイプの場合はPitTrapをデフォルトに
                from pyrogue.entities.traps.trap import PitTrap

                trap = PitTrap(x, y)

            # 隠し状態を設定
            trap.is_hidden = is_hidden

            return trap

        except Exception as e:
            self.context.add_message(f"Error deserializing trap: {e}")
            return None
