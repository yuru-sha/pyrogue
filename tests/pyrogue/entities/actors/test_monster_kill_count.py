"""モンスター討伐数のテストスクリプト"""

import pytest
from pyrogue.core.game_logic import GameLogic
from pyrogue.entities.actors.monster import Monster


def test_monster_kill_count():
    """モンスター討伐数が正しくカウントされるかテスト"""

    # GameLogicを初期化
    game_logic = GameLogic()
    game_logic.setup_new_game()

    print(f"初期討伐数: {game_logic.player.monsters_killed}")

    # テスト用モンスターを作成
    test_monster = Monster(
        x=game_logic.player.x + 1,
        y=game_logic.player.y,
        name="Test Bat",
        char='b',
        hp=1,  # 1発で倒せるように
        max_hp=1,
        attack=1,
        defense=0,
        level=1,
        exp_value=10,
        view_range=3,
        color=(255, 255, 255)
    )

    # モンスターをフロアに追加
    floor_data = game_logic.get_current_floor_data()
    if floor_data and hasattr(floor_data, 'monster_spawner'):
        floor_data.monster_spawner.monsters.append(test_monster)
        print(f"テストモンスターを ({test_monster.x}, {test_monster.y}) に配置")

    print(f"戦闘前討伐数: {game_logic.player.monsters_killed}")

    # 戦闘を実行
    success = game_logic.combat_manager.handle_player_attack(test_monster, game_logic.context)

    print(f"戦闘後討伐数: {game_logic.player.monsters_killed}")
    print(f"戦闘成功: {success}")
    print(f"モンスターHP: {test_monster.hp}")

    # 討伐数が増加しているかチェック
    if game_logic.player.monsters_killed > 0:
        print("✅ モンスター討伐数のカウントは正常に動作しています")
    else:
        print("❌ モンスター討伐数がカウントされていません")


if __name__ == "__main__":
    test_monster_kill_count()
