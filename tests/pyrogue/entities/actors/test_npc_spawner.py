"""
NPCSpawner のテストモジュール。

NPC配置システムの機能テストを提供します。
"""

from unittest.mock import Mock

import numpy as np
from pyrogue.entities.actors.npc import NPCDisposition, NPCType
from pyrogue.entities.actors.npc_spawner import NPCSpawner


class TestNPCSpawner:
    """NPCSpawner のテストクラス。"""

    def test_npc_spawner_initialization(self):
        """NPCSpawnerの初期化テスト。"""
        spawner = NPCSpawner(floor=5)

        assert spawner.floor == 5
        assert spawner.npcs == []
        assert spawner.occupied_positions == set()

    def test_calculate_npc_count(self):
        """NPC数計算のテスト。"""
        # 1階: 基本3個
        spawner = NPCSpawner(floor=1)
        count = spawner._calculate_npc_count()
        assert 2 <= count <= 4  # 3 + random(-1,1)

        # 10階: 基本2個
        spawner = NPCSpawner(floor=10)
        count = spawner._calculate_npc_count()
        assert 1 <= count <= 3  # 2 + random(-1,1)

        # 20階: 基本1個
        spawner = NPCSpawner(floor=20)
        count = spawner._calculate_npc_count()
        assert 0 <= count <= 2  # 1 + random(-1,1)

    def test_get_npc_type_for_special_room(self):
        """特別な部屋に対応するNPCタイプ取得のテスト。"""
        spawner = NPCSpawner(floor=1)

        # 特別な部屋とNPCタイプの対応
        assert spawner._get_npc_type_for_special_room("treasure_room") == NPCType.MERCHANT
        assert spawner._get_npc_type_for_special_room("shrine") == NPCType.PRIEST
        assert spawner._get_npc_type_for_special_room("laboratory") == NPCType.MAGE
        assert spawner._get_npc_type_for_special_room("library") == NPCType.MAGE
        assert spawner._get_npc_type_for_special_room("armory") == NPCType.GUARD

        # 存在しない部屋タイプ
        assert spawner._get_npc_type_for_special_room("unknown_room") is None

    def test_get_random_npc_type(self):
        """ランダムNPCタイプ取得のテスト。"""
        spawner = NPCSpawner(floor=1)

        # 複数回実行して有効なタイプが返されることを確認
        valid_types = [
            NPCType.MERCHANT,
            NPCType.VILLAGER,
            NPCType.GUARD,
            NPCType.PRIEST,
            NPCType.MAGE,
        ]

        for _ in range(10):
            npc_type = spawner._get_random_npc_type()
            assert npc_type in valid_types

    def test_is_valid_position(self):
        """位置の有効性判定のテスト。"""
        spawner = NPCSpawner(floor=1)

        # 5x5のテストダンジョン（0=床、1=壁）
        dungeon_tiles = np.array(
            [
                [1, 1, 1, 1, 1],
                [1, 0, 0, 0, 1],
                [1, 0, 0, 0, 1],
                [1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1],
            ]
        )

        # 有効な位置（床タイル）
        assert spawner._is_valid_position(1, 1, dungeon_tiles) == True
        assert spawner._is_valid_position(2, 2, dungeon_tiles) == True

        # 無効な位置（壁タイル）
        assert spawner._is_valid_position(0, 0, dungeon_tiles) == False
        assert spawner._is_valid_position(4, 4, dungeon_tiles) == False

        # 境界外
        assert spawner._is_valid_position(-1, 1, dungeon_tiles) == False
        assert spawner._is_valid_position(5, 1, dungeon_tiles) == False

        # 占有済み位置
        spawner.occupied_positions.add((1, 1))
        assert spawner._is_valid_position(1, 1, dungeon_tiles) == False

    def test_create_npc_merchant(self):
        """商人NPC作成のテスト。"""
        spawner = NPCSpawner(floor=1)

        npc = spawner._create_npc(NPCType.MERCHANT, (10, 15))

        assert npc is not None
        assert npc.x == 10
        assert npc.y == 15
        assert npc.npc_type == NPCType.MERCHANT
        assert npc.disposition == NPCDisposition.FRIENDLY
        assert npc.color == (255, 255, 0)  # 金色
        assert npc.inventory is not None  # 商人はインベントリを持つ
        assert len(npc.inventory.items) > 0  # 商品を持っている

    def test_create_npc_priest(self):
        """僧侶NPC作成のテスト。"""
        spawner = NPCSpawner(floor=1)

        npc = spawner._create_npc(NPCType.PRIEST, (5, 8))

        assert npc is not None
        assert npc.x == 5
        assert npc.y == 8
        assert npc.npc_type == NPCType.PRIEST
        assert npc.disposition == NPCDisposition.FRIENDLY
        assert npc.color == (255, 255, 255)  # 白色
        assert npc.inventory is None  # 僧侶はインベントリを持たない

    def test_create_npc_other_types(self):
        """その他のNPCタイプ作成のテスト。"""
        spawner = NPCSpawner(floor=1)

        # 魔術師
        mage = spawner._create_npc(NPCType.MAGE, (3, 4))
        assert mage is not None
        assert mage.npc_type == NPCType.MAGE
        assert mage.disposition == NPCDisposition.NEUTRAL
        assert mage.color == (128, 0, 128)  # 紫色

        # 警備員
        guard = spawner._create_npc(NPCType.GUARD, (7, 9))
        assert guard is not None
        assert guard.npc_type == NPCType.GUARD
        assert guard.disposition == NPCDisposition.NEUTRAL
        assert guard.color == (169, 169, 169)  # 灰色

        # 村人
        villager = spawner._create_npc(NPCType.VILLAGER, (12, 6))
        assert villager is not None
        assert villager.npc_type == NPCType.VILLAGER
        assert villager.disposition == NPCDisposition.FRIENDLY
        assert villager.color == (139, 69, 19)  # 茶色

    def test_create_merchant_inventory(self):
        """商人のインベントリ作成のテスト。"""
        spawner = NPCSpawner(floor=1)

        inventory = spawner._create_merchant_inventory()

        assert inventory is not None
        assert len(inventory.items) >= 3  # 最低3個のアイテム
        assert len(inventory.items) <= 6  # 最大6個のアイテム

        # 多様なアイテムタイプが含まれていることを確認
        item_types = {item.__class__.__name__ for item in inventory.items}
        assert len(item_types) > 1  # 複数の種類のアイテム

    def test_spawn_special_room_npcs(self):
        """特別な部屋のNPC配置のテスト。"""
        spawner = NPCSpawner(floor=1)

        # ダンジョンタイルのモック
        dungeon_tiles = np.zeros((10, 10))

        # 特別な部屋のモック
        special_room = Mock()
        special_room.is_special = True
        special_room.room_type = "treasure_room"
        special_room.x = 2
        special_room.y = 2
        special_room.width = 4
        special_room.height = 4

        # 通常の部屋のモック
        normal_room = Mock()
        normal_room.is_special = False

        rooms = [special_room, normal_room]

        # NPCを配置
        spawner._spawn_special_room_npcs(dungeon_tiles, rooms)

        # 商人NPCが配置されていることを確認
        assert len(spawner.npcs) == 1
        npc = spawner.npcs[0]
        assert npc.npc_type == NPCType.MERCHANT
        assert 2 <= npc.x <= 6  # x + width の範囲内
        assert 2 <= npc.y <= 6  # y + height の範囲内

    def test_get_npc_at_position(self):
        """位置指定でのNPC取得のテスト。"""
        spawner = NPCSpawner(floor=1)

        # NPCを作成して追加
        npc = spawner._create_npc(NPCType.VILLAGER, (5, 7))
        spawner.npcs.append(npc)

        # 位置でNPCを取得
        found_npc = spawner.get_npc_at_position(5, 7)
        assert found_npc == npc

        # 存在しない位置
        not_found = spawner.get_npc_at_position(10, 10)
        assert not_found is None

    def test_clear_npcs(self):
        """NPCクリアのテスト。"""
        spawner = NPCSpawner(floor=1)

        # NPCを追加
        npc = spawner._create_npc(NPCType.VILLAGER, (5, 7))
        spawner.npcs.append(npc)
        spawner.occupied_positions.add((5, 7))

        # クリア前の状態確認
        assert len(spawner.npcs) == 1
        assert len(spawner.occupied_positions) == 1

        # クリア実行
        spawner.clear_npcs()

        # クリア後の状態確認
        assert len(spawner.npcs) == 0
        assert len(spawner.occupied_positions) == 0

    def test_name_generation(self):
        """名前生成のテスト。"""
        spawner = NPCSpawner(floor=1)

        # 各タイプの名前生成
        merchant_name = spawner._generate_merchant_name()
        priest_name = spawner._generate_priest_name()
        mage_name = spawner._generate_mage_name()
        guard_name = spawner._generate_guard_name()
        villager_name = spawner._generate_villager_name()

        # 文字列が返されることを確認
        assert isinstance(merchant_name, str)
        assert isinstance(priest_name, str)
        assert isinstance(mage_name, str)
        assert isinstance(guard_name, str)
        assert isinstance(villager_name, str)

        # 名前が空でないことを確認
        assert len(merchant_name) > 0
        assert len(priest_name) > 0
        assert len(mage_name) > 0
        assert len(guard_name) > 0
        assert len(villager_name) > 0
