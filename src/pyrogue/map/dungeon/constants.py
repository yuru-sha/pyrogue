"""
ダンジョン生成関連の定数定義。

このモジュールは、ダンジョン生成アルゴリズムで使用される
定数値を集約管理します。
"""

from __future__ import annotations


# BSP (Binary Space Partitioning) 関連定数
class BSPConstants:
    """BSPダンジョン生成の定数。"""

    # BSP分割設定
    DEPTH = 10
    MIN_SIZE = 8  # 部屋間の最小間隔3マス以上を確保するため
    FULL_ROOMS = False  # False: ランダムサイズ部屋, True: ノード全体を部屋に

    # 部屋サイズ設定
    MIN_ROOM_SIZE = 4
    MAX_ROOM_SIZE_RATIO = 0.8  # ノードサイズに対する部屋の最大比率


# ドア生成関連定数
class DoorConstants:
    """ドア生成の定数。"""

    # ドア状態の確率（パーセンテージ）
    SECRET_DOOR_CHANCE = 0.10  # 10% 隠し扉
    OPEN_DOOR_CHANCE = 0.30  # 30% オープンドア
    CLOSED_DOOR_CHANCE = 0.60  # 60% クローズドドア

    # ドア配置の制限
    MIN_DOOR_DISTANCE = 2  # ドア間の最小距離
    MAX_DOORS_PER_ROOM = 4  # 部屋あたりの最大ドア数

    # 隠し扉探索の設定
    HIDDEN_DOOR_SEARCH_RANGE = 2  # 隠し扉探索範囲


# 通路生成関連定数
class CorridorConstants:
    """通路生成の定数。"""

    # 通路接続設定
    ADDITIONAL_CONNECTION_CHANCE = 0.20  # 20% 追加接続作成確率
    MIN_ROOMS_FOR_ADDITIONAL = 3  # 追加接続に必要な最小部屋数

    # 通路の幅・形状
    CORRIDOR_WIDTH = 1
    MIN_CORRIDOR_LENGTH = 2

    # 接続点選択の設定
    CONNECTION_POINT_OFFSET = 2  # 部屋境界からの接続点オフセット


# 迷路生成関連定数
class MazeConstants:
    """迷路生成の定数。"""

    # 迷路密度設定
    MIN_FLOOR_DENSITY = 0.10  # 最小床密度（10%）
    MAX_FLOOR_DENSITY = 0.40  # 最大床密度（40%）
    TARGET_FLOOR_DENSITY = 0.25  # 目標床密度（25%）

    # セルラーオートマタ設定
    CELLULAR_AUTOMATA_ITERATIONS = 5  # 反復回数
    BIRTH_LIMIT = 4  # 生成閾値
    DEATH_LIMIT = 3  # 消滅閾値

    # 迷路階層設定
    MAZE_FLOORS = [7, 13, 19]  # 必ず迷路になる階層


# 部屋生成関連定数
class RoomConstants:
    """部屋生成の定数。"""

    # 部屋サイズ設定
    MIN_ROOM_WIDTH = 4
    MIN_ROOM_HEIGHT = 4
    MAX_ROOM_WIDTH = 20
    MAX_ROOM_HEIGHT = 15

    # 部屋間の距離設定
    MIN_ROOM_DISTANCE = 3  # 部屋間の最小距離
    ROOM_PADDING = 1  # 部屋周囲の余白

    # 特殊部屋の設定
    SPECIAL_ROOM_CHANCE = 0.15  # 15% 特殊部屋生成確率


# 階段配置関連定数
class StairsConstants:
    """階段配置の定数。"""

    # 階段配置の制限
    MIN_STAIRS_DISTANCE = 10  # 上り階段と下り階段の最小距離
    STAIRS_ROOM_PREFERENCE = 0.8  # 80% 部屋内配置、20% 通路配置

    # 階段周囲の安全エリア
    STAIRS_SAFE_RADIUS = 2  # 階段周囲の安全半径


# 検証関連定数
class ValidationConstants:
    """ダンジョン検証の定数。"""

    # 到達可能性チェック
    MIN_REACHABLE_TILES = 0.30  # 最小到達可能タイル比率（30%）
    MAX_ISOLATED_AREAS = 3  # 最大孤立エリア数

    # 部屋検証
    MIN_ROOMS_PER_FLOOR = 4  # フロアあたりの最小部屋数
    MAX_ROOMS_PER_FLOOR = 12  # フロアあたりの最大部屋数

    # 通路検証
    MIN_CORRIDOR_COUNT = 3  # 最小通路数
    MAX_CORRIDOR_COMPLEXITY = 0.5  # 最大通路複雑度
