# PyRogue 開発ガイド

## 前提

- Python 3.12以上
- uv
- TCOD（GUIを実行する場合）

依存関係を同期します。

```bash
uv sync --locked --extra dev
```

## 実行

```bash
uv run --locked game --cli --seed 1234
uv run --locked game --seed 1234
```

ゲームルールを直接扱う場合は次のAPIを使います。

```python
from pyrogue.core.game_state import GameState

game = GameState(seed=1234)
result = game.execute("h")
print(result.message)
```

## テストと検証

```bash
make verify
```

個別に実行する場合も lockfile を固定します。

```bash
uv run --locked --extra dev pytest -q
uv run --locked --extra dev ruff check src tests
uv run --locked --extra dev ruff format --check src tests
uv run --locked --extra dev mypy src/pyrogue/core/rogue_game.py src/pyrogue/core/game_state.py
uv run --locked --extra dev python -m compileall -q src tests
```

変更後は、少なくとも変更箇所のテストと全体テストを実行します。生成ロジックを変更した
場合は、複数seedで全階の階段到達性も確認します。

CLIの機能テストは `scripts/cli_test.sh` が固定seedで実行します。再現確認のseedを変える場合は、例えば `CLI_TEST_SEED=20260908 make test-cli` とします。

## 実装ルール

- `GameState`のRNG以外でゲーム中の乱数を生成しない。
- CLIとGUIで個別のルールを実装せず、`GameState.execute`を共有する。
- 死亡後は `SaveManager.finalize_death` を共有し、canonical状態のサマリーを表示して死亡セーブを削除する。勝利時は削除しない。
- UIへTCODのConsole、色、画像、タイル型をゲーム状態から持ち込まない。
- 保存形式を変更するときは `GAME_VERSION` と互換性検査を同時に更新する。
- 勝利・死亡サマリーには `player.deepest_floor` を使い、`current_floor` と混同しない。
- 死亡・勝利は終端状態として扱い、死亡セーブをロードしない。
- GUIのTabによるFOV切替は表示専用とし、FOV無効化中も探索済み状態を更新しない。
- FOV無効化中のGUIコマンドは GameState.execute の update_explored=False を介し、自動可視化だけを抑止する。
- SPECにない機能、依存関係、抽象化を追加しない。

## 変更の流れ

1. `SPEC.md`の該当要件を確認する。
2. canonicalなゲーム状態とコマンドを小さく変更する。
3. 表示が必要なら `DisplayCell` とレンダラーだけを更新する。
4. JSONラウンドトリップ、決定性、勝敗、既存テストを確認する。
5. 実機や異なる端末での確認が必要な場合は、未実施であることを報告する。
