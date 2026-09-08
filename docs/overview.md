# PyRogue プロジェクト概要

**現在の仕様: 0.3.0**

文書の入口は [docs/README.md](README.md) です。このページは概要だけを扱います。

PyRogueは、Rogue 5.4を参考にしたPython 3.12製のテキストローグライクです。目的は、
古典的な探索、資源管理、ターン制戦闘、パーマデスを、テスト可能な小さなゲーム状態として
実装することです。

## プレイヤーの目標

ダンジョンを26階まで下り、Amulet of Yendorを回収し、階段を使って地上へ戻ります。
途中でHP、食料、装備、インベントリ容量を管理します。勝利・死亡サマリーの階層は最深到達階を
示し、`current_floor` の現在位置とは分けて扱います。死亡したゲームは再開できません。

## 起動方法

```bash
uv run --locked game --cli --seed 1234
uv run --locked game --seed 1234
```

CLIとGUIは同じ `GameState` コマンドを使います。seedを指定しない場合は自動生成seedを使います。

## 実装の見方

```text
GameState -> DisplayCell -> CLI / GameRenderer
```

ゲームルールは `src/pyrogue/core/rogue_game.py` に集約し、CLIとGUIの表示層は同じ表示セルを文字へ変換します。
この境界により、TCOD画面を起動せずに階層生成、戦闘、保存、勝敗をテストできます。

## 仕様と記録

- 正本: [SPEC.md](../SPEC.md)
- 詳細設計: [game_design_document.md](game_design_document.md)
- 実装構造: [architecture.md](architecture.md)
- 機能一覧: [features.md](features.md)
- 開発手順: [development.md](development.md)
