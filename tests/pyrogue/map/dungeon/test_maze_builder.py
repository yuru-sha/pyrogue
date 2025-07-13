"""
迷路ビルダーのテスト。

迷路階層生成システムの動作確認を行う。
"""

import numpy as np
from pyrogue.map.dungeon.maze_builder import MazeBuilder
from pyrogue.map.tile import Floor, Wall


class TestMazeBuilder:
    """迷路ビルダーのテストクラス。"""

    def test_maze_builder_initialization(self):
        """迷路ビルダーの初期化テスト。"""
        builder = MazeBuilder(50, 30, complexity=0.8)
        assert builder.width == 50
        assert builder.height == 30
        assert builder.complexity == 0.8
        assert builder.rooms == []

    def test_basic_maze_generation(self):
        """基本的な迷路生成テスト。"""
        builder = MazeBuilder(40, 30, complexity=0.6)
        tiles = np.full((30, 40), Wall(), dtype=object)

        # 迷路を生成
        rooms = builder.build_dungeon(tiles)

        # 部屋は存在しない（空リスト）
        assert len(rooms) == 0

        # 境界が壁であることを確認
        for x in range(40):
            assert isinstance(tiles[0, x], Wall)  # 上端
            assert isinstance(tiles[29, x], Wall)  # 下端

        for y in range(30):
            assert isinstance(tiles[y, 0], Wall)  # 左端
            assert isinstance(tiles[y, 39], Wall)  # 右端

    def test_maze_has_floors(self):
        """迷路に床が存在することを確認。"""
        builder = MazeBuilder(40, 30, complexity=0.5)
        tiles = np.full((30, 40), Wall(), dtype=object)

        builder.build_dungeon(tiles)

        # 床タイルの数をカウント
        floor_count = sum(
            1 for y in range(30) for x in range(40) if isinstance(tiles[y, x], Floor)
        )

        # 床タイルが存在することを確認
        assert floor_count > 0

        # 床の割合が妥当な範囲内にあることを確認
        total_tiles = 30 * 40
        floor_ratio = floor_count / total_tiles
        assert 0.015 <= floor_ratio <= 0.5  # 1.5%～50%の範囲（迷路は狭い通路が特徴）

    def test_maze_connectivity(self):
        """迷路の連結性をテスト。"""
        builder = MazeBuilder(30, 20, complexity=0.7)
        tiles = np.full((20, 30), Wall(), dtype=object)

        builder.build_dungeon(tiles)

        # 床タイルの連結成分を確認
        floor_positions = []
        for y in range(20):
            for x in range(30):
                if isinstance(tiles[y, x], Floor):
                    floor_positions.append((x, y))

        if floor_positions:
            # 最初の床タイルから他の床タイルへの到達可能性を確認
            visited = set()
            stack = [floor_positions[0]]

            while stack:
                x, y = stack.pop()
                if (x, y) in visited:
                    continue
                visited.add((x, y))

                # 4方向をチェック
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < 30
                        and 0 <= ny < 20
                        and isinstance(tiles[ny, nx], Floor)
                        and (nx, ny) not in visited
                    ):
                        stack.append((nx, ny))

            # 大部分の床タイルが連結していることを確認
            connected_ratio = len(visited) / len(floor_positions)
            assert connected_ratio >= 0.8  # 80%以上が連結

    def test_different_complexity_levels(self):
        """異なる複雑度レベルのテスト。"""
        low_complexity = MazeBuilder(30, 20, complexity=0.3)
        high_complexity = MazeBuilder(30, 20, complexity=0.9)

        tiles_low = np.full((20, 30), Wall(), dtype=object)
        tiles_high = np.full((20, 30), Wall(), dtype=object)

        low_complexity.build_dungeon(tiles_low)
        high_complexity.build_dungeon(tiles_high)

        # 床タイルの数をカウント
        floor_count_low = sum(
            1
            for y in range(20)
            for x in range(30)
            if isinstance(tiles_low[y, x], Floor)
        )
        floor_count_high = sum(
            1
            for y in range(20)
            for x in range(30)
            if isinstance(tiles_high[y, x], Floor)
        )

        # 両方とも床タイルが存在することを確認
        assert floor_count_low > 0
        assert floor_count_high > 0

    def test_small_maze_generation(self):
        """小さな迷路の生成テスト。"""
        builder = MazeBuilder(15, 10, complexity=0.5)
        tiles = np.full((10, 15), Wall(), dtype=object)

        # 例外が発生しないことを確認
        rooms = builder.build_dungeon(tiles)
        assert len(rooms) == 0

    def test_large_maze_generation(self):
        """大きな迷路の生成テスト。"""
        builder = MazeBuilder(80, 60, complexity=0.6)
        tiles = np.full((60, 80), Wall(), dtype=object)

        # 例外が発生しないことを確認
        rooms = builder.build_dungeon(tiles)
        assert len(rooms) == 0

    def test_maze_builder_reset(self):
        """迷路ビルダーのリセット機能テスト。"""
        builder = MazeBuilder(30, 20, complexity=0.5)
        tiles = np.full((20, 30), Wall(), dtype=object)

        builder.build_dungeon(tiles)

        # リセット実行
        builder.reset()

        # 状態がリセットされたことを確認
        assert builder.rooms == []

    def test_maze_builder_statistics(self):
        """迷路ビルダーの統計情報テスト。"""
        builder = MazeBuilder(30, 20, complexity=0.7)

        stats = builder.get_statistics()

        # 統計情報の構造を確認
        assert "builder_type" in stats
        assert "complexity" in stats
        assert "room_count" in stats
        assert "corridor_only" in stats

        assert stats["builder_type"] == "Maze"
        assert stats["complexity"] == 0.7
        assert stats["room_count"] == 0
        assert stats["corridor_only"] is True

    def test_maze_boundary_integrity(self):
        """迷路の境界整合性テスト。"""
        builder = MazeBuilder(25, 15, complexity=0.4)
        tiles = np.full((15, 25), Wall(), dtype=object)

        builder.build_dungeon(tiles)

        # 境界がすべて壁であることを確認
        for x in range(25):
            assert isinstance(tiles[0, x], Wall)  # 上端
            assert isinstance(tiles[14, x], Wall)  # 下端

        for y in range(15):
            assert isinstance(tiles[y, 0], Wall)  # 左端
            assert isinstance(tiles[y, 24], Wall)  # 右端

    def test_maze_no_isolated_floors(self):
        """孤立した床タイルがないことを確認。"""
        builder = MazeBuilder(30, 20, complexity=0.6)
        tiles = np.full((20, 30), Wall(), dtype=object)

        builder.build_dungeon(tiles)

        # 各床タイルが隣接する床タイルを持つことを確認
        for y in range(1, 19):  # 境界を除く
            for x in range(1, 29):
                if isinstance(tiles[y, x], Floor):
                    # 隣接する床タイルの数をカウント
                    adjacent_floors = 0
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if isinstance(tiles[ny, nx], Floor):
                            adjacent_floors += 1

                    # 完全に孤立していないことを確認
                    # （迷路の性質上、デッドエンドは許可されるが、完全孤立は不可）
                    assert adjacent_floors > 0
