"""
光源アイテムシステムのテスト。

このテストは、光源アイテム（たいまつ、ランタン、光る指輪）が
正常に動作することを確認します。
"""

import pytest

from pyrogue.entities.items.light_items import (
    Torch, Lantern, LightRing, LightManager
)


class TestTorch:
    """たいまつクラスのテストクラス。"""

    def test_torch_initialization(self):
        """たいまつの初期化テスト。"""
        torch = Torch(duration=150)

        assert torch.name == "Torch"
        assert torch.light_radius == 4
        assert torch.duration == 150
        assert torch.remaining_duration == 150
        assert torch.intensity == 0.8
        assert not torch.is_lit
        assert torch.stackable
        assert torch.max_stack == 5

    def test_torch_light_usage(self):
        """たいまつの点灯テスト。"""
        torch = Torch(duration=100)

        # 点灯前
        assert torch.get_light_radius() == 0
        assert not torch.is_lit

        # 点灯
        result = torch.use_light()
        assert result
        assert torch.is_lit
        assert torch.get_light_radius() == 4

    def test_torch_fuel_consumption(self):
        """たいまつの燃料消費テスト。"""
        torch = Torch(duration=10)
        torch.use_light()  # 点灯

        # 燃料消費
        torch.consume_fuel(5)
        assert torch.remaining_duration == 5
        assert torch.is_lit
        assert torch.get_light_radius() == 4

        # 燃料切れ
        torch.consume_fuel(10)
        assert torch.remaining_duration == 0
        assert not torch.is_lit
        assert torch.get_light_radius() == 0
        assert torch.is_depleted()

    def test_torch_depleted_usage(self):
        """燃料切れたいまつの使用テスト。"""
        torch = Torch(duration=0)

        # 燃料切れの場合は点灯できない
        result = torch.use_light()
        assert not result
        assert not torch.is_lit
        assert torch.get_light_radius() == 0


class TestLantern:
    """ランタンクラスのテストクラス。"""

    def test_lantern_initialization(self):
        """ランタンの初期化テスト。"""
        lantern = Lantern(duration=400)

        assert lantern.name == "Lantern"
        assert lantern.light_radius == 6
        assert lantern.duration == 400
        assert lantern.remaining_duration == 400
        assert lantern.intensity == 1.0
        assert not lantern.is_lit
        assert not lantern.stackable

    def test_lantern_superior_light(self):
        """ランタンの優れた光性能テスト。"""
        lantern = Lantern()
        torch = Torch()

        lantern.use_light()
        torch.use_light()

        # ランタンの方が明るい
        assert lantern.get_light_radius() > torch.get_light_radius()
        assert lantern.intensity > torch.intensity

    def test_lantern_fuel_consumption(self):
        """ランタンの燃料消費テスト。"""
        lantern = Lantern(duration=20)
        lantern.use_light()

        # 燃料消費
        lantern.consume_fuel(10)
        assert lantern.remaining_duration == 10
        assert lantern.is_lit

        # 燃料切れ
        lantern.consume_fuel(15)
        assert lantern.remaining_duration == 0
        assert not lantern.is_lit
        assert lantern.is_depleted()


class TestLightRing:
    """光る指輪クラスのテストクラス。"""

    def test_light_ring_initialization(self):
        """光る指輪の初期化テスト。"""
        ring = LightRing(light_radius=5)

        assert ring.name == "Ring of Light"
        assert ring.light_radius == 5
        assert ring.duration == -1  # 無限
        assert ring.intensity == 0.6
        assert not ring.is_equipped
        assert not ring.stackable

    def test_light_ring_eternal_light(self):
        """光る指輪の永続光テスト。"""
        ring = LightRing()

        # 装備前
        assert ring.get_light_radius() == 0
        assert not ring.is_depleted()

        # 装備
        result = ring.use_light()
        assert result
        assert ring.is_equipped
        assert ring.get_light_radius() == 3

        # 永続的に光る（燃料切れしない）
        assert not ring.is_depleted()

    def test_light_ring_no_fuel_consumption(self):
        """光る指輪の燃料消費なしテスト。"""
        ring = LightRing()
        ring.use_light()

        initial_light = ring.get_light_radius()

        # 時間が経過しても光は変わらない（consume_fuelメソッドが存在しない）
        assert ring.get_light_radius() == initial_light
        assert not ring.is_depleted()


class TestLightManager:
    """光源管理システムのテストクラス。"""

    def test_light_manager_initialization(self):
        """光源マネージャーの初期化テスト。"""
        manager = LightManager()

        assert manager.active_light_sources == []
        assert manager.get_total_light_radius() == 0
        assert not manager.has_active_light()

    def test_add_remove_light_sources(self):
        """光源の追加・削除テスト。"""
        manager = LightManager()
        torch = Torch()
        lantern = Lantern()

        # 光源を追加
        manager.add_light_source(torch)
        assert len(manager.active_light_sources) == 1

        manager.add_light_source(lantern)
        assert len(manager.active_light_sources) == 2

        # 重複追加は無視される
        manager.add_light_source(torch)
        assert len(manager.active_light_sources) == 2

        # 光源を削除
        manager.remove_light_source(torch)
        assert len(manager.active_light_sources) == 1
        assert lantern in manager.active_light_sources

    def test_total_light_radius_calculation(self):
        """合計光量計算テスト。"""
        manager = LightManager()

        torch = Torch()
        torch.use_light()

        lantern = Lantern()
        lantern.use_light()

        ring = LightRing()
        ring.use_light()

        # 光源を追加
        manager.add_light_source(torch)
        manager.add_light_source(lantern)
        manager.add_light_source(ring)

        # 最大光量が採用される（ランタンが最も明るい）
        total_radius = manager.get_total_light_radius()
        assert total_radius == 6  # ランタンの光量

    def test_light_intensity_calculation(self):
        """光の強度計算テスト。"""
        manager = LightManager()

        torch = Torch()
        torch.use_light()

        lantern = Lantern()
        lantern.use_light()

        manager.add_light_source(torch)
        manager.add_light_source(lantern)

        # 最大強度が採用される（ランタンが最も強い）
        intensity = manager.get_light_intensity()
        assert intensity == 1.0  # ランタンの強度

    def test_fuel_consumption_management(self):
        """燃料消費管理テスト。"""
        manager = LightManager()

        torch = Torch(duration=5)
        torch.use_light()

        lantern = Lantern(duration=10)
        lantern.use_light()

        ring = LightRing()
        ring.use_light()

        manager.add_light_source(torch)
        manager.add_light_source(lantern)
        manager.add_light_source(ring)

        # 燃料消費
        manager.consume_fuel(3)

        assert torch.remaining_duration == 2
        assert lantern.remaining_duration == 7
        assert len(manager.active_light_sources) == 3  # まだ全て有効

        # たいまつが燃料切れになるまで消費
        manager.consume_fuel(5)

        # たいまつは自動的に削除される
        assert len(manager.active_light_sources) == 2
        assert torch not in manager.active_light_sources
        assert lantern in manager.active_light_sources
        assert ring in manager.active_light_sources

    def test_has_active_light(self):
        """有効な光源の存在チェックテスト。"""
        manager = LightManager()

        # 光源なし
        assert not manager.has_active_light()

        # 点灯していない光源
        torch = Torch()
        manager.add_light_source(torch)
        assert not manager.has_active_light()

        # 点灯した光源
        torch.use_light()
        assert manager.has_active_light()

        # 燃料切れ
        torch.consume_fuel(torch.remaining_duration + 1)
        manager.consume_fuel(1)  # マネージャーで削除処理
        assert not manager.has_active_light()

    def test_statistics_generation(self):
        """統計情報生成テスト。"""
        manager = LightManager()

        torch = Torch()
        torch.use_light()

        lantern = Lantern()
        lantern.use_light()

        manager.add_light_source(torch)
        manager.add_light_source(lantern)

        stats = manager.get_statistics()

        assert stats["active_sources"] == 2
        assert stats["total_light_radius"] == 6  # ランタンの光量
        assert stats["light_intensity"] == 1.0  # ランタンの強度
        assert stats["has_light"]
        assert "Torch" in stats["light_sources"]
        assert "Lantern" in stats["light_sources"]


class TestLightSourceIntegration:
    """光源アイテムの統合テストクラス。"""

    def test_different_light_sources_comparison(self):
        """異なる光源の比較テスト。"""
        torch = Torch(duration=100)
        lantern = Lantern(duration=200)
        ring = LightRing(light_radius=4)

        # 全て点灯/装備
        torch.use_light()
        lantern.use_light()
        ring.use_light()

        # 性能比較
        assert lantern.get_light_radius() > torch.get_light_radius()
        assert lantern.get_light_radius() > ring.get_light_radius()
        assert lantern.intensity > torch.intensity
        assert lantern.intensity > ring.intensity

        # 持続性比較
        assert ring.duration == -1  # 無限
        assert lantern.duration > torch.duration

    def test_light_source_lifecycle(self):
        """光源のライフサイクルテスト。"""
        manager = LightManager()

        # たいまつの短期使用
        torch = Torch(duration=3)
        torch.use_light()
        manager.add_light_source(torch)

        assert manager.has_active_light()

        # 燃料消費でたいまつが切れる
        manager.consume_fuel(5)
        assert not manager.has_active_light()

        # ランタンの長期使用
        lantern = Lantern(duration=100)
        lantern.use_light()
        manager.add_light_source(lantern)

        manager.consume_fuel(50)
        assert manager.has_active_light()  # まだ有効

        # 指輪の永続使用
        ring = LightRing()
        ring.use_light()
        manager.add_light_source(ring)

        manager.consume_fuel(1000)  # 大量消費
        assert manager.has_active_light()  # 指輪は永続
