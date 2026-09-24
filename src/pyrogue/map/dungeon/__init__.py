"""
ダンジョン生成システム - Builder Pattern実装。

このモジュールは、Builder Patternを使用して責務を分離した
ダンジョン生成システムを提供します。

主要なコンポーネント:
    - DungeonDirector: 全体的な構築プロセスの管理
    - DoorManager: ドア配置
    - StairsManager: 階段配置
    - ValidationManager: 生成結果の検証
"""

# 主要なクラスをエクスポート
from .corridor_builder import Corridor
from .director import DungeonDirector
from .door_manager import DoorManager
from .maze_builder import MazeBuilder
from .room_builder import Room
from .stairs_manager import StairsManager
from .validation_manager import ValidationManager

__all__ = [
    "Corridor",
    "DoorManager",
    "DungeonDirector",
    "MazeBuilder",
    "Room",
    "StairsManager",
    "ValidationManager",
]
