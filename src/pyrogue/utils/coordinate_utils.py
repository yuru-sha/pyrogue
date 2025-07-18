"""
座標計算ユーティリティ。

このモジュールは、座標関連の計算処理を提供します。
距離計算、視界判定、移動処理などの共通機能を集約します。
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogue.core.managers.game_context import GameContext


def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """
    2点間のユークリッド距離を計算。

    Args:
    ----
        x1, y1: 点1の座標
        x2, y2: 点2の座標

    Returns:
    -------
        ユークリッド距離

    """
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def calculate_manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """
    2点間のマンハッタン距離を計算。

    Args:
    ----
        x1, y1: 点1の座標
        x2, y2: 点2の座標

    Returns:
    -------
        マンハッタン距離

    """
    return abs(x2 - x1) + abs(y2 - y1)


def normalize_direction(dx: int, dy: int) -> tuple[int, int]:
    """
    方向ベクトルを正規化（-1, 0, 1に制限）。

    Args:
    ----
        dx: X方向の移動量
        dy: Y方向の移動量

    Returns:
    -------
        正規化された方向ベクトル

    """
    normalized_dx = 0
    normalized_dy = 0

    if dx != 0:
        normalized_dx = dx // abs(dx)
    if dy != 0:
        normalized_dy = dy // abs(dy)

    return normalized_dx, normalized_dy


def get_line_points(x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
    """
    ブレゼンハム線分アルゴリズムで線上の点を取得。

    Args:
    ----
        x1, y1: 開始点の座標
        x2, y2: 終了点の座標

    Returns:
    -------
        線上の点のリスト

    """
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    x_inc = 1 if x1 < x2 else -1
    y_inc = 1 if y1 < y2 else -1
    error = dx - dy

    while True:
        points.append((x, y))
        if x == x2 and y == y2:
            break

        e2 = 2 * error
        if e2 > -dy:
            error -= dy
            x += x_inc
        if e2 < dx:
            error += dx
            y += y_inc

    return points


def is_adjacent(x1: int, y1: int, x2: int, y2: int, threshold: float = 1.5) -> bool:
    """
    2点が隣接しているかチェック。

    Args:
    ----
        x1, y1: 点1の座標
        x2, y2: 点2の座標
        threshold: 隣接とみなす距離の閾値

    Returns:
    -------
        隣接している場合True

    """
    return calculate_distance(x1, y1, x2, y2) <= threshold


def is_within_bounds(x: int, y: int, width: int, height: int) -> bool:
    """
    座標が境界内にあるかチェック。

    Args:
    ----
        x: X座標
        y: Y座標
        width: 幅
        height: 高さ

    Returns:
    -------
        境界内にある場合True

    """
    return 0 <= x < width and 0 <= y < height


def get_neighbors(x: int, y: int, include_diagonals: bool = True) -> list[tuple[int, int]]:
    """
    指定座標の隣接する座標を取得。

    Args:
    ----
        x: 中心のX座標
        y: 中心のY座標
        include_diagonals: 斜め方向を含むかどうか

    Returns:
    -------
        隣接座標のリスト

    """
    neighbors = []

    # 上下左右
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    # 斜め方向
    if include_diagonals:
        directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

    for dx, dy in directions:
        neighbors.append((x + dx, y + dy))

    return neighbors


def get_direction_to_target(start_x: int, start_y: int, target_x: int, target_y: int) -> tuple[int, int]:
    """
    目標座標への方向を取得。

    Args:
    ----
        start_x, start_y: 開始座標
        target_x, target_y: 目標座標

    Returns:
    -------
        方向ベクトル（正規化済み）

    """
    dx = target_x - start_x
    dy = target_y - start_y
    return normalize_direction(dx, dy)


def has_line_of_sight(x1: int, y1: int, x2: int, y2: int, context: GameContext) -> bool:
    """
    2点間に視界があるかチェック。

    Args:
    ----
        x1, y1: 開始点の座標
        x2, y2: 終了点の座標
        context: ゲームコンテキスト

    Returns:
    -------
        視界がある場合True

    """
    floor_data = context.get_current_floor_data()
    if not floor_data:
        return False

    # ブレゼンハム線分アルゴリズムで視界チェック
    points = get_line_points(x1, y1, x2, y2)

    for x, y in points[1:-1]:  # 開始点と終了点は除外
        if is_within_bounds(x, y, floor_data.tiles.shape[1], floor_data.tiles.shape[0]):
            tile = floor_data.tiles[y, x]
            if not getattr(tile, "transparent", True):
                return False

    return True


def get_positions_within_radius(
    center_x: int, center_y: int, radius: int, include_center: bool = False
) -> list[tuple[int, int]]:
    """
    指定半径内の全座標を取得。

    Args:
    ----
        center_x: 中心のX座標
        center_y: 中心のY座標
        radius: 半径
        include_center: 中心座標を含むかどうか

    Returns:
    -------
        半径内の座標リスト

    """
    positions = []

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if not include_center and dx == 0 and dy == 0:
                continue

            if calculate_distance(0, 0, dx, dy) <= radius:
                positions.append((center_x + dx, center_y + dy))

    return positions
