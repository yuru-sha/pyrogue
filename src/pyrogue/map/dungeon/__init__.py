"""
ダンジョン生成システム - Builder Pattern実装。

このモジュールは、Builder Patternを使用して責務を分離した
ダンジョン生成システムを提供します。

各コンポーネント:
    - DungeonDirector: 全体的な構築プロセスの管理
    - RoomBuilder: 部屋生成専用
    - CorridorBuilder: 通路生成専用
    - DoorManager: ドア配置専用
    - SpecialRoomBuilder: 特別部屋専用
    - StairsManager: 階段配置専用
    - ValidationManager: 検証専用
"""

# 主要なクラスをエクスポート
from .director import DungeonDirector
from .room_builder import Room, RoomBuilder
from .corridor_builder import Corridor, CorridorBuilder
from .door_manager import DoorManager
from .special_room_builder import SpecialRoomBuilder
from .stairs_manager import StairsManager
from .validation_manager import ValidationManager

__all__ = [
    'DungeonDirector',
    'Room',
    'RoomBuilder',
    'Corridor',
    'CorridorBuilder',
    'DoorManager',
    'SpecialRoomBuilder',
    'StairsManager',
    'ValidationManager',
]
