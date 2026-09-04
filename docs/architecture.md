# PyRogue アーキテクチャ

**対象バージョン: 0.3.0**

## 方針

ゲームのルールと表示を分離します。ルールは標準ライブラリだけで実行でき、CLIとGUIは
同じコマンドAPIを呼び出します。乱数は `GameState` が所有する `random.Random` に集約し、
seedと入力列から再現可能にします。

## データフロー

```text
入力 (CLI / TCOD)
        |
        v
GameState.execute(command, args)
        |
        +--> floor / player / monsters / items / traps
        |
        v
GameState.display_cells()
        |
        v
GameRenderer (文字・色)
```

`GameState` は地形、階層キャッシュ、プレイヤー、エンティティ、インベントリ、戦闘、
飢え、視界、メッセージ、勝敗状態、乱数状態を所有します。`DisplayCell` は位置、地形、
可視性、探索済み状態、エンティティ、描画優先度を表す表示用の値です。

## 主要モジュール

- `pyrogue.core.rogue_game`: canonicalなデータモデル、生成、ルール、コマンド、JSON変換。
- `pyrogue.core.game_state`: canonical APIの公開用re-export。
- `pyrogue.core.cli_engine`: 文字入力を `GameState.execute` に渡すCLIアダプター。
- `pyrogue.ui.screens.game_screen`: GUIライフサイクルとcanonical状態の保持。
- `pyrogue.ui.components.input_handler`: TCODイベントを同じコマンドへ変換。
- `pyrogue.ui.components.game_renderer`: `DisplayCell` を画面へ描画。
- `pyrogue.core.save_manager`: JSONセーブ、チェックサム、バージョン拒否、パーマデス検査。

旧来のTCODゲームモジュールは既存利用者との互換性のため残していますが、新しいCLI起動、
seed指定、GUIの描画・入力・保存はcanonical経路を使用します。

## 階層生成

`DungeonGenerator` はseed付きRNGを受け取り、通常階では部屋を作ってL字通路で接続します。
7、13、19階では迷路を生成します。生成後に歩行可能領域から階段への到達性を検査し、
壊れた階はゲーム開始前にエラーにします。

## 表示と視界

ゲーム状態はTCODへ依存せず、Bresenhamベースの視界計算で可視セルと探索済みセルを更新します。
表示優先度はプレイヤー、モンスター、アイテム、トラップ、地形の順です。未探索セルは空白、
探索済みだが現在見えないセルは地形だけを表示します。

## 保存形式

セーブはJSONです。仕様バージョン、seed、全階層、プレイヤー、エンティティ、メッセージ、
IDカウンタ、RNG状態、死亡・勝利・パーマデス状態を保存します。`spec_version` が現在の
`0.3.0` と一致しないファイルは自動移行せず、互換性エラーとして拒否します。
