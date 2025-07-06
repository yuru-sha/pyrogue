"""
ゲーム状態モジュール。

このモジュールは、ゲームの各状態を定義し、状態遷移と
渡り制御を管理するためのEnumを提供します。

Example:
    >>> if game.state == GameStates.PLAYERS_TURN:
    ...     handle_player_input()

"""

from enum import Enum, auto


class GameStates(Enum):
    """
    ゲームの状態を表す列挙型。

    ゲームの進行状態、メニューシステム、インベントリ管理等の
    各状態を定義し、ゲームエンジンが適切な処理を選択できるようにします。

    States:
        MENU: メインメニュー状態
        PLAYERS_TURN: プレイヤーのターン
        ENEMY_TURN: 敵のターン
        PLAYER_DEAD: プレイヤー死亡状態
        GAME_OVER: ゲームオーバー状態
        SHOW_INVENTORY: インベントリ表示状態
        DROP_INVENTORY: アイテム破棄状態
        TARGETING: ターゲット選択状態
        LEVEL_UP: レベルアップ状態
        CHARACTER_SCREEN: キャラクター情報状態
        EXIT: ゲーム終了状態
    """

    MENU = auto()  # メインメニュー表示中
    PLAYERS_TURN = auto()  # プレイヤーの入力待ち
    ENEMY_TURN = auto()  # 敵の行動処理中
    PLAYER_DEAD = auto()  # プレイヤー死亡時の処理
    GAME_OVER = auto()  # ゲームオーバー画面表示
    VICTORY = auto()  # ゲーム勝利画面表示
    SHOW_INVENTORY = auto()  # インベントリ一覧表示
    DROP_INVENTORY = auto()  # アイテム破棄モード
    SHOW_MAGIC = auto()  # 魔法一覧表示
    TARGETING = auto()  # ターゲット選択モード
    LEVEL_UP = auto()  # レベルアップ時の選択
    CHARACTER_SCREEN = auto()  # キャラクター情報表示
    EXIT = auto()  # ゲーム終了シグナル
