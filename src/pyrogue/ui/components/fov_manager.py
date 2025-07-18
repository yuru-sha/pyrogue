"""
FOV（視界）管理コンポーネント。

このモジュールは、GameScreen から分離された視界システムを担当します。
FOV計算、可視範囲の管理、探索済みエリアの更新を行います。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import tcod
from tcod import libtcodpy

from pyrogue.constants import GameConstants
from pyrogue.map.tile import Wall

if TYPE_CHECKING:
    from pyrogue.ui.screens.game_screen import GameScreen


class FOVManager:
    """
    FOV（視界）システムの管理クラス。

    プレイヤーの視界計算、可視範囲の管理、探索済みエリアの更新を担当します。

    Attributes
    ----------
        game_screen: メインのゲームスクリーンへの参照
        fov_enabled: FOV表示の有効/無効フラグ
        fov_map: FOV計算用のマップ
        visible: 現在視界内のタイル
        fov_radius: 視界半径

    """

    def __init__(self, game_screen: GameScreen) -> None:
        """
        FOVマネージャーを初期化。

        Args:
        ----
            game_screen: メインのゲームスクリーンインスタンス

        """
        self.game_screen = game_screen
        self.fov_enabled = True
        self.fov_radius = GameConstants.DEFAULT_FOV_RADIUS
        self.base_fov_radius = GameConstants.DEFAULT_FOV_RADIUS  # 基本FOV半径

        # FOV計算用のマップを初期化
        self.fov_map = tcod.map.Map(width=game_screen.dungeon_width, height=game_screen.dungeon_height)

        # 可視範囲を初期化
        self.visible = np.full(
            (game_screen.dungeon_height, game_screen.dungeon_width),
            fill_value=False,
            dtype=bool,
        )

    def update_fov(self) -> None:
        """
        FOVマップとプレイヤーの視界を更新。

        プレイヤーの現在位置に基づいて視界を再計算し、
        探索済みエリアを更新します。
        """
        if not self.fov_enabled:
            # FOVが無効の場合は全体を可視にする
            self.visible.fill(True)
            return

        # FOVマップを更新
        self._update_fov_map()

        # プレイヤーの位置でFOVを計算
        player = self.game_screen.player
        if player:
            self._compute_fov(player.x, player.y)

    def _update_fov_map(self) -> None:
        """
        FOV計算用のマップを現在のダンジョン状態に更新。

        壁とその他のタイルの透明度を設定します。
        """
        floor_data = self.game_screen.game_logic.get_current_floor_data()
        if not floor_data or not floor_data.tiles.size:
            return

        # 全てのタイルを透明（通行可能）として初期化
        transparent = np.ones(
            (self.game_screen.dungeon_height, self.game_screen.dungeon_width),
            dtype=bool,
        )
        walkable = np.ones(
            (self.game_screen.dungeon_height, self.game_screen.dungeon_width),
            dtype=bool,
        )

        # 壁と閉じたドアは不透明で通行不可
        for y in range(floor_data.tiles.shape[0]):
            for x in range(floor_data.tiles.shape[1]):
                tile = floor_data.tiles[y, x]
                if isinstance(tile, Wall):
                    transparent[y, x] = False
                    walkable[y, x] = False
                elif hasattr(tile, "transparent") and hasattr(tile, "walkable"):
                    # ドアなどのタイルの透明度・通行可能性を使用
                    transparent[y, x] = tile.transparent
                    walkable[y, x] = tile.walkable

        # FOVマップに設定
        self.fov_map.transparent[:] = transparent
        self.fov_map.walkable[:] = walkable

    def _compute_fov(self, x: int, y: int) -> None:
        """
        指定座標からのFOVを計算。

        Args:
        ----
            x: プレイヤーのX座標
            y: プレイヤーのY座標

        """
        # 可視範囲をリセット
        self.visible.fill(False)

        # 暗い部屋での視界制限を適用
        effective_radius = self._calculate_effective_fov_radius(x, y)

        # FOV計算
        self.fov_map.compute_fov(x, y, radius=effective_radius, algorithm=libtcodpy.FOV_SHADOW)

        # 結果を可視範囲配列にコピー
        self.visible[:] = self.fov_map.fov[:]

        # 現在の可視範囲を探索済みとして記録
        self.game_screen.game_logic.update_explored_tiles(self.visible)

    def _calculate_effective_fov_radius(self, x: int, y: int) -> int:
        """
        暗い部屋での効果的なFOV半径を計算。

        Args:
        ----
            x: プレイヤーのX座標
            y: プレイヤーのY座標

        Returns:
        -------
            効果的なFOV半径

        """
        # 現在の階層データを取得
        floor_data = self.game_screen.game_logic.get_current_floor_data()
        if not floor_data:
            return self.base_fov_radius

        # ダンジョンディレクターから暗い部屋情報を取得
        dungeon_director = getattr(floor_data, "dungeon_director", None)
        if not dungeon_director or not hasattr(dungeon_director, "dark_room_builder"):
            return self.base_fov_radius

        dark_room_builder = dungeon_director.dark_room_builder

        # プレイヤーの光源状態を取得
        player = self.game_screen.game_logic.player
        has_light = self._player_has_light_source(player)
        light_radius = self._get_player_light_radius(player)

        # 暗い部屋での視界範囲を計算
        return dark_room_builder.get_visibility_range_at(
            x, y, getattr(floor_data, "rooms", []), has_light, light_radius
        )

    def _player_has_light_source(self, player) -> bool:
        """
        プレイヤーが光源を持っているかチェック。

        Args:
        ----
            player: プレイヤーオブジェクト

        Returns:
        -------
            光源を持っている場合True

        """
        # プレイヤーのインベントリから光源アイテムを検索
        if hasattr(player, "inventory") and hasattr(player.inventory, "items"):
            for item in player.inventory.items:
                if hasattr(item, "get_light_radius") and item.get_light_radius() > 0:
                    return True

        return False

    def _get_player_light_radius(self, player) -> int:
        """
        プレイヤーの光源半径を取得。

        Args:
        ----
            player: プレイヤーオブジェクト

        Returns:
        -------
            光源半径

        """
        max_radius = 0

        if hasattr(player, "inventory") and hasattr(player.inventory, "items"):
            for item in player.inventory.items:
                if hasattr(item, "get_light_radius"):
                    radius = item.get_light_radius()
                    max_radius = max(max_radius, radius)

        return max_radius if max_radius > 0 else self.base_fov_radius

    def toggle_fov(self) -> None:
        """
        FOV表示の有効/無効を切り替え。

        Returns
        -------
            現在のFOV状態のメッセージ

        """
        self.fov_enabled = not self.fov_enabled
        self.update_fov()

        if self.fov_enabled:
            return "FOV enabled"
        return "FOV disabled"

    def set_fov_radius(self, radius: int) -> None:
        """
        FOV半径を設定。

        Args:
        ----
            radius: 新しい視界半径

        """
        self.fov_radius = max(1, min(radius, GameConstants.MAX_FOV_RADIUS))  # 1-20の範囲に制限
        self.update_fov()

    def is_visible(self, x: int, y: int) -> bool:
        """
        指定座標が現在視界内にあるかチェック。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            視界内にある場合True

        """
        if not (0 <= x < self.game_screen.dungeon_width and 0 <= y < self.game_screen.dungeon_height):
            return False
        return self.visible[y, x]

    def is_explored(self, x: int, y: int) -> bool:
        """
        指定座標が探索済みかチェック。

        Args:
        ----
            x: X座標
            y: Y座標

        Returns:
        -------
            探索済みの場合True

        """
        if not (0 <= x < self.game_screen.dungeon_width and 0 <= y < self.game_screen.dungeon_height):
            return False
        return self.game_screen.game_logic.get_explored_tiles()[y, x]
