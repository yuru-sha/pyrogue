# PyRogue

Python と TCOD を使用して作成されたローグライクゲーム。

## 特徴

- 手続き的生成によるダンジョン
- ターンベースの戦闘システム
- パーマデス（永続的な死）システム
- 探索要素の重視
- すべてのアイテムは識別済み状態
- モンスターはA-Zの英大文字で表現

## 必要条件

- Python 3.12
- uv (パッケージマネージャー)

## インストール

```bash
# 初回セットアップ（仮想環境の作成と依存関係のインストール）
make setup

# または、既存の環境に依存関係をインストール
make install

# ゲームの起動
make run

# 開発モードでの起動（デバッグログ有効）
make dev
```

## 開発者向け

開発に必要な追加パッケージがインストールされます：

- Black (コードフォーマッター)
- isort (importの整理)
- pylint (リンター)
- mypy (型チェック)
- pytest (テスト)

開発用コマンド：

```bash
# コードのフォーマット
make format

# リントとタイプチェック
make lint

# テストの実行
make test

# ファイル変更の監視と自動テスト
make watch-test

# ファイル変更の監視と自動フォーマット
make watch-format

# ファイル変更の監視と自動再起動
make watch-run
```

詳細な開発者向けガイドは[docs/development.md](docs/development.md)を参照してください。

## 操作方法

- 移動: viキー (h,j,k,l,y,u,b,n) またはカーソルキー
- インベントリ: i
- 装備: w
- 使用: q
- ヘルプ: ?

## 開発環境

- Python 3.12
- TCOD
- NumPy
