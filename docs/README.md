# PyRogue ドキュメント入口

## 現在の正本

| 知りたいこと | 参照先 |
| --- | --- |
| 要件、スコープ、対象外、受け入れ条件 | [`SPEC.md`](../SPEC.md) |
| プロジェクト概要 | [`overview.md`](overview.md) |
| 現在のモジュール境界とデータフロー | [`architecture.md`](architecture.md) と `src/pyrogue/` |
| 現在の機能境界 | [`features.md`](features.md) |
| セットアップ、実行、検証 | [`development.md`](development.md)、`Makefile` |
| テストの実際の契約 | `tests/` と `scripts/cli_test.sh` |

`SPEC.md` が製品要件の正本です。設計・実装・テストの記述が要件と食い違う場合は、要件を優先し、必要なら差分を明示してから更新します。

## 旧資料・提案資料

次の資料は作成時点の設計、タスク、QA記録、または提案です。現在のテスト数、機能一覧、アーキテクチャ、完了状態の根拠には使わず、履歴を調査するときだけ参照します。

- `task.md`, `task-phase1.md`
- `technical_specification.md`
- `quality_assurance.md`
- `cli_test_scenarios.md`
- `combat_balance_v0.2.0_completed.md`, `combat_balance_proposal.md`
- `components/`, `sequence_diagrams.md`, `state_machine_diagrams.md`
- `game_design_document.md`（`SPEC.md` と内容を照合する補助資料）

旧資料を現行仕様として再利用する必要が生じた場合は、先に `SPEC.md`、実装、テストとの整合を確認してください。

## エージェント機能

- 再現可能なプロジェクトSkill: `.agents/skills/pyrogue-verify/SKILL.md`
- `.agents/agent-capabilities/` と `.codex/agents/` は外部絶対パスへのマシンローカルリンクであり、`.gitignore` でコミット対象から除外します。
