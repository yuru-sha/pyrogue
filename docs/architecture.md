# PyRogue アーキテクチャ

**対象バージョン: 0.3.1**

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
CLI文字レンダラー / TCOD GameRenderer (文字・色)
```

`GameState` は地形、階層キャッシュ、プレイヤー、エンティティ、インベントリ、戦闘、
飢え、視界、メッセージ、勝敗状態、乱数状態を所有します。`DisplayCell` は位置、地形、
可視性、探索済み状態、エンティティ、描画優先度を表す表示用の値です。

GUIは各フレームを表示してからTCODイベントを待ちます。同じ待機周期で複数のキー入力が届いた場合も、
各入力を処理した直後に現在の画面を描画・表示してから次のキー入力を処理し、メッセージ表示を行動に同期します。

## 主要モジュール

- `pyrogue.core.rogue_game`: canonicalなデータモデル、生成、ルール、コマンド、JSON変換。
- `pyrogue.core.game_state`: canonical APIの公開用re-export。
- `pyrogue.core.cli_engine`: 文字入力を `GameState.execute` に渡すCLIアダプター。
- `pyrogue.presentation.display_renderer`: CLIとGUIが共有する表示セルから文字への変換。
- `pyrogue.ui.screens.game_screen`: GUIライフサイクルとcanonical状態の保持。
- `pyrogue.ui.components.input_handler`: TCODイベントを同じコマンドへ変換。
- `pyrogue.ui.components.game_renderer`: `DisplayCell` を画面へ描画。
- `pyrogue.ui.screens.options_screen`: Rogue操作のオプション表示。表示専用の変更はターン進行から分離します。
- `pyrogue.core.save_manager`: JSONセーブ、チェックサム、バージョン拒否、パーマデス検査。死亡時は `finalize_death` をCLI/GUIで共有する。

旧GameLogic、独自コマンドハンドラー、旧エンティティ、旧ダンジョン生成器は削除しました。
GUIのインベントリも `GameState.player.inventory` を表示し、投擲・杖の使用は選択した
アイテムIDを `GameState.execute` に渡します。方向が必要な操作だけ方向も渡し、light の杖は
方向を要求しません。選択途中の情報だけをUIが保持します。

床上アイテムは通常移動時に取得し、浮遊中は取得しません。容量は `inpack` 相当で、food /
potion / scroll は数量ごと、同一group IDのdagger・arrow・dart・shurikenはグループごとに枠を
使います。他の所持品は各1枠です。金貨は所持金へ直接加算します。

## 階層生成

`DungeonGenerator` はseed付きRNGを使い、Rogue 5.4.4の9区画、重複を拒否する部屋欠落選択、迷路の深さ優先掘削、乱択全域木・追加通路を生成します。GameStateは部屋ごとの金貨・モンスター、通常アイテム、罠、下り階段、帰還用上り階段、主人公の順に配置し、上下階段の到達性を確認します。上り階段と、その階段位置に主人公を固定しない配置は本作の帰還進行・原作準拠の開始位置のための設計です。

## 表示と視界

ゲーム状態はTCODへ依存せず、Bresenhamベースの視界計算で可視セルと探索済みセルを更新します。
表示優先度はプレイヤー、モンスター、アイテム、トラップ、地形の順です。未探索セルは空白、
探索済みだが現在見えないセルは地形だけを表示します。
GUIは最上段に最新メッセージ1行、最下段に階層とステータスを表示し、その間にマップを描画します。
これはRogue 5.4.4のメッセージ行とステータス行の配置に合わせています。
GUIのTabはFOV表示を一時的に切り替えます。無効化中は`GameState.display_cells(show_all=True)`を
canonicalな表示経路から呼び出して全体を描画しますが、探索済み集合は更新しません。

GUIのコマンドアダプターはFOV無効化中、GameState.execute の update_explored=False を使い、
自動的な可視範囲の記録だけを抑止します。この実行オプションはセーブ対象ではなく、
lightやmagic mappingなど明示的なゲーム効果は引き続き適用します。

## 保存形式

セーブはJSONです。仕様バージョン、seed、全階層、プレイヤー、エンティティ、メッセージ、
IDカウンタ、RNG状態、死亡・勝利・パーマデス状態を保存します。`spec_version` が現在の
`0.3.12` と一致しないファイルは自動移行せず、互換性エラーとして拒否します。階層内の
未発見の隠し扉・通路、罠の発見状態、アイテム識別・呼称、一時効果、モンスターの行動状態、
slow 行動ビット、wandering monster の残り待機ターンと4ターン確認周期、食料生成間隔、
失神・bear restraint・睡眠・静穏ターン数、Hungry/Weak/Faintの永続空腹状態も保存します。
アイテムの group ID・取得履歴も保存し、同じ武器グループをロード後も統合可能にします。
静穏回復はレベル別のターン cadence に従い、
戦闘や回復量の加算（最大HPで切り捨てられる場合を含む）で静穏状態をリセットします。`current_floor` は現在位置、
`player.deepest_floor` は到達記録であり、勝利・死亡サマリーは後者を表示します。
現在の`spec_version`を持つ場合も、必須フィールド（`seed`、`player`、`floors`、`rng_state`、
`wander_turns`、`wander_checks`）を欠く旧形式は、ファイルを変更せず互換性エラーとして拒否します。
`player.hunger_state` は0〜3の必須値として保存します。失神状態は残りターンが0になっても維持し、食事で通常状態に戻します。
復元前にcanonicalな`GameState`への変換まで検証し、成功した場合だけセーブを単一使用として消費します。
消費マーカーを先に記録してからメインセーブ、バックアップ、メタデータ、チェックサムを削除するため、
新しいセーブを開始するときに消費マーカーと古い保存ファイルを除去してから書き込みます。
互換性検査または状態復元に失敗した場合は、元の保存データと回復用ファイルを保持します。
