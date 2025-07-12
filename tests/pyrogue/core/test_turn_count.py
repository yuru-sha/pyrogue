"""ターン数カウントのテストスクリプト"""

from pyrogue.core.game_logic import GameLogic


def test_turn_count():
    """ターン数が正しくカウントされるかテスト"""
    # GameLogicを初期化
    game_logic = GameLogic()
    game_logic.setup_new_game()

    print(f"初期ターン数: {game_logic.player.turns_played}")

    # 移動を実行（ターンが進行するはず）
    success = game_logic.handle_player_move(1, 0)  # 東に移動

    print(f"移動後ターン数: {game_logic.player.turns_played}")
    print(f"移動成功: {success}")

    # もう一度移動
    success = game_logic.handle_player_move(0, 1)  # 南に移動

    print(f"2回目移動後ターン数: {game_logic.player.turns_played}")
    print(f"2回目移動成功: {success}")

    # ターン数が増加しているかチェック
    if game_logic.player.turns_played > 0:
        print("✅ ターン数のカウントは正常に動作しています")
    else:
        print("❌ ターン数がカウントされていません")


if __name__ == "__main__":
    test_turn_count()
