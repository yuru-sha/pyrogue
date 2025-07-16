"""
線描画ユーティリティのテストモジュール。

このモジュールは、LineDrawerクラスの機能を包括的にテストし、
線描画処理の正確性を検証します。
"""

from unittest.mock import Mock, call

import numpy as np
from pyrogue.map.dungeon.line_drawer import LineDrawer


class TestLineDrawer:
    """線描画器のテストクラス。"""

    def test_init(self):
        """初期化のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        assert drawer.tile_placer == tile_placer

    def test_draw_horizontal_line_basic(self):
        """基本的な水平線描画のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_horizontal_line(tiles, 10, 15, 12)

        # 6つの点（10-15）で呼び出されることを確認
        assert tile_placer.call_count == 6

        # 呼び出し順序と境界フラグを確認
        expected_calls = [
            call(tiles, 10, 12, True),  # 最初の点：境界
            call(tiles, 11, 12, True),  # 中間点：通常
            call(tiles, 12, 12, True),  # 中間点：通常
            call(tiles, 13, 12, True),  # 中間点：通常
            call(tiles, 14, 12, True),  # 中間点：通常
            call(tiles, 15, 12, True),  # 最後の点：境界
        ]
        tile_placer.assert_has_calls(expected_calls)

    def test_draw_horizontal_line_reverse(self):
        """逆順水平線描画のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_horizontal_line(tiles, 10, 15, 12, reverse=True)

        # 6つの点で呼び出されることを確認
        assert tile_placer.call_count == 6

        # 逆順の呼び出しを確認
        expected_calls = [
            call(tiles, 15, 12, True),  # 最初の点（逆順）：境界
            call(tiles, 14, 12, True),  # 中間点：通常
            call(tiles, 13, 12, True),  # 中間点：通常
            call(tiles, 12, 12, True),  # 中間点：通常
            call(tiles, 11, 12, True),  # 中間点：通常
            call(tiles, 10, 12, True),  # 最後の点（逆順）：境界
        ]
        tile_placer.assert_has_calls(expected_calls)

    def test_draw_horizontal_line_with_boundary_placer(self):
        """境界ドア配置器付き水平線描画のテスト。"""
        tile_placer = Mock()
        boundary_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_horizontal_line(tiles, 10, 12, 12, boundary_door_placer=boundary_placer)

        # 境界位置では boundary_placer が呼ばれる
        boundary_placer.assert_has_calls(
            [
                call(tiles, 10, 12, True),  # 最初の点
                call(tiles, 12, 12, True),  # 最後の点
            ]
        )

        # 中間位置では tile_placer が呼ばれる
        tile_placer.assert_has_calls(
            [
                call(tiles, 11, 12, True),  # 中間点
            ]
        )

    def test_draw_vertical_line_basic(self):
        """基本的な垂直線描画のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_vertical_line(tiles, 12, 10, 15)

        # 6つの点（10-15）で呼び出されることを確認
        assert tile_placer.call_count == 6

        # 呼び出し順序と境界フラグを確認
        expected_calls = [
            call(tiles, 12, 10, True),  # 最初の点：境界
            call(tiles, 12, 11, True),  # 中間点：通常
            call(tiles, 12, 12, True),  # 中間点：通常
            call(tiles, 12, 13, True),  # 中間点：通常
            call(tiles, 12, 14, True),  # 中間点：通常
            call(tiles, 12, 15, True),  # 最後の点：境界
        ]
        tile_placer.assert_has_calls(expected_calls)

    def test_draw_vertical_line_reverse(self):
        """逆順垂直線描画のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_vertical_line(tiles, 12, 10, 15, reverse=True)

        # 6つの点で呼び出されることを確認
        assert tile_placer.call_count == 6

        # 逆順の呼び出しを確認
        expected_calls = [
            call(tiles, 12, 15, True),  # 最初の点（逆順）：境界
            call(tiles, 12, 14, True),  # 中間点：通常
            call(tiles, 12, 13, True),  # 中間点：通常
            call(tiles, 12, 12, True),  # 中間点：通常
            call(tiles, 12, 11, True),  # 中間点：通常
            call(tiles, 12, 10, True),  # 最後の点（逆順）：境界
        ]
        tile_placer.assert_has_calls(expected_calls)

    def test_draw_vertical_line_with_boundary_placer(self):
        """境界ドア配置器付き垂直線描画のテスト。"""
        tile_placer = Mock()
        boundary_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_vertical_line(tiles, 12, 10, 12, boundary_door_placer=boundary_placer)

        # 境界位置では boundary_placer が呼ばれる
        boundary_placer.assert_has_calls(
            [
                call(tiles, 12, 10, True),  # 最初の点
                call(tiles, 12, 12, True),  # 最後の点
            ]
        )

        # 中間位置では tile_placer が呼ばれる
        tile_placer.assert_has_calls(
            [
                call(tiles, 12, 11, True),  # 中間点
            ]
        )

    def test_draw_connection_line_horizontal_first(self):
        """水平優先のL字接続線描画のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_connection_line(tiles, 10, 10, 15, 15, horizontal_first=True)

        # 水平線（10,10）→（15,10）と垂直線（15,10）→（15,15）が描画される
        # 合計で水平線6点 + 垂直線6点 = 12点
        assert tile_placer.call_count == 12

    def test_draw_connection_line_vertical_first(self):
        """垂直優先のL字接続線描画のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_connection_line(tiles, 10, 10, 15, 15, horizontal_first=False)

        # 垂直線（10,10）→（10,15）と水平線（10,15）→（15,15）が描画される
        # 合計で垂直線6点 + 水平線6点 = 12点
        assert tile_placer.call_count == 12

    def test_draw_connection_line_with_boundary_placer(self):
        """境界ドア配置器付きL字接続線描画のテスト。"""
        tile_placer = Mock()
        boundary_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_connection_line(tiles, 10, 10, 12, 12, horizontal_first=True, boundary_door_placer=boundary_placer)

        # 境界位置で boundary_placer が呼ばれることを確認
        # 水平線の両端 + 垂直線の両端 = 4回（ただし交点は重複）
        assert boundary_placer.call_count >= 3

    def test_single_point_line(self):
        """1点のみの線描画のテスト。"""
        tile_placer = Mock()
        drawer = LineDrawer(tile_placer)

        tiles = np.zeros((25, 80), dtype=object)
        drawer.draw_horizontal_line(tiles, 10, 10, 12)

        # 1点のみなので1回だけ呼ばれる
        assert tile_placer.call_count == 1
        tile_placer.assert_called_once_with(tiles, 10, 12, True)

    def test_coordinate_order_independence(self):
        """座標順序の独立性のテスト。"""
        tile_placer1 = Mock()
        tile_placer2 = Mock()
        drawer1 = LineDrawer(tile_placer1)
        drawer2 = LineDrawer(tile_placer2)

        tiles = np.zeros((25, 80), dtype=object)

        # 同じ線を異なる順序で描画
        drawer1.draw_horizontal_line(tiles, 10, 15, 12)
        drawer2.draw_horizontal_line(tiles, 15, 10, 12)

        # 両方とも同じ回数呼ばれる
        assert tile_placer1.call_count == tile_placer2.call_count

        # 呼び出された座標も同じ（順序は異なるが）
        called_coords1 = {(args[0][1], args[0][2]) for args in tile_placer1.call_args_list}
        called_coords2 = {(args[0][1], args[0][2]) for args in tile_placer2.call_args_list}
        assert called_coords1 == called_coords2
