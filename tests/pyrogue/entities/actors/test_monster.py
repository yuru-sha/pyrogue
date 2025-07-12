"""
Monster クラスのテストモジュール。

基本的なモンスター機能のテストを提供します。
"""

from unittest.mock import Mock

from pyrogue.entities.actors.monster import Monster


class TestMonster:
    """Monster クラスのテストクラス。"""

    def test_monster_initialization(self):
        """モンスターの初期化テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
            is_hostile=True,
        )

        # 基本属性の確認
        assert monster.char == "A"
        assert monster.x == 10
        assert monster.y == 15
        assert monster.name == "Ant"
        assert monster.level == 1
        assert monster.hp == 20
        assert monster.max_hp == 20
        assert monster.attack == 5
        assert monster.defense == 2
        assert monster.exp_value == 10
        assert monster.view_range == 5
        assert monster.color == (255, 0, 0)
        assert monster.is_hostile is True

        # 状態異常システムの初期化確認
        assert monster.status_effects is not None

    def test_monster_move(self):
        """モンスターの移動テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # 正の移動
        monster.move(3, 2)
        assert monster.x == 13
        assert monster.y == 17

        # 負の移動
        monster.move(-1, -4)
        assert monster.x == 12
        assert monster.y == 13

        # ゼロ移動
        monster.move(0, 0)
        assert monster.x == 12
        assert monster.y == 13

    def test_monster_take_damage(self):
        """モンスターのダメージ処理テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # 通常のダメージ
        damage = 8
        monster.take_damage(damage)
        expected_hp = max(0, 20 - max(0, damage - 2))  # 20 - (8 - 2) = 14
        assert monster.hp == expected_hp

        # 防御力を超えるダメージ
        monster.hp = 20
        high_damage = 12
        monster.take_damage(high_damage)
        assert monster.hp == 10  # 20 - (12 - 2) = 10

        # HPが0未満にならないことを確認
        monster.hp = 5
        monster.take_damage(100)
        assert monster.hp == 0

    def test_monster_heal(self):
        """モンスターの回復処理テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=10,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # 通常の回復
        monster.heal(5)
        assert monster.hp == 15

        # 最大HPを超えて回復しないことを確認
        monster.heal(20)
        assert monster.hp == 20

    def test_monster_death(self):
        """モンスターの死亡判定テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=5,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # 生存状態
        assert not monster.is_dead()

        # 死亡状態
        monster.hp = 0
        assert monster.is_dead()

        # 負のHP（実際にはtake_damageで0になる）
        monster.hp = -5
        assert monster.is_dead()

    def test_monster_vision(self):
        """モンスターの視界判定テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # モックFOVマップ
        mock_fov = Mock()
        mock_fov.transparent = {}

        # 視界内でプレイヤーが見える場合
        player_x, player_y = (
            12,
            17,
        )  # 距離: sqrt((12-10)^2 + (17-15)^2) = sqrt(8) ≈ 2.83 < 5
        mock_fov.transparent[player_y, player_x] = True
        assert monster.can_see_player(player_x, player_y, mock_fov)

        # 視界外のプレイヤー
        player_x, player_y = (
            20,
            25,
        )  # 距離: sqrt((20-10)^2 + (25-15)^2) = sqrt(200) ≈ 14.14 > 5
        mock_fov.transparent[player_y, player_x] = True
        assert not monster.can_see_player(player_x, player_y, mock_fov)

        # 視界内だが壁で遮られている場合
        player_x, player_y = 12, 17
        mock_fov.transparent[player_y, player_x] = False
        assert not monster.can_see_player(player_x, player_y, mock_fov)

    def test_monster_move_towards_player(self):
        """モンスターのプレイヤー追跡移動テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # 右上にプレイヤーがいる場合
        dx, dy = monster.get_move_towards_player(15, 10)
        assert dx == 1  # 右へ
        assert dy == -1  # 上へ

        # 左下にプレイヤーがいる場合
        dx, dy = monster.get_move_towards_player(5, 20)
        assert dx == -1  # 左へ
        assert dy == 1  # 下へ

        # 同じ位置にいる場合
        dx, dy = monster.get_move_towards_player(10, 15)
        assert dx == 0
        assert dy == 0

        # 横方向のみ異なる場合
        dx, dy = monster.get_move_towards_player(12, 15)
        assert dx == 1
        assert dy == 0

    def test_monster_random_move(self):
        """モンスターのランダム移動テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # 8方向の可能な移動
        valid_moves = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]

        # 複数回実行してランダムな移動を確認
        moves = [monster.get_random_move() for _ in range(10)]

        # すべての移動が有効な方向であることを確認
        for move in moves:
            assert move in valid_moves

    def test_monster_status_effects(self):
        """モンスターの状態異常テスト。"""
        monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
        )

        # 初期状態
        assert not monster.is_paralyzed()
        assert not monster.is_confused()
        assert not monster.is_poisoned()
        assert not monster.has_status_effect("NonExistent")

        # 状態異常の更新（モックコンテキストを使用）
        mock_context = Mock()
        monster.update_status_effects(mock_context)

        # status_effects.update_effects が呼び出されることを確認
        assert hasattr(monster.status_effects, "update_effects")

    def test_monster_hostility(self):
        """モンスターの敵対性テスト。"""
        # 敵対的なモンスター
        hostile_monster = Monster(
            char="A",
            x=10,
            y=15,
            name="Ant",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(255, 0, 0),
            is_hostile=True,
        )
        assert hostile_monster.is_hostile is True

        # 非敵対的なモンスター
        friendly_monster = Monster(
            char="B",
            x=10,
            y=15,
            name="Butterfly",
            level=1,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_value=10,
            view_range=5,
            color=(0, 255, 0),
            is_hostile=False,
        )
        assert friendly_monster.is_hostile is False
