# AI-Friendly Logger System

このプロジェクトにVibe Logger概念を取り入れたAI最適化ログシステムを実装しました。

## 🌟 概要

**Vibe Logger**の思想：
> "VibeCoding (AI駆動開発)では、デバッグの質はLLMにどれだけコンテキストを提供できるかで決まる"

このシステムは、従来の人間向けログから、**AI分析に最適化された構造化ログ**への転換を実現します。

## 🚀 主要機能

### 1. 構造化JSONログ形式
```json
{
  "timestamp": "2025-07-10T08:30:00.123Z",
  "correlation_id": "unique-id",
  "operation": {
    "tool": "Edit",
    "type": "CODE_MODIFICATION",
    "command": "edit file.py",
    "exit_code": 0,
    "files": [
      {
        "path": "/path/to/file.py",
        "size": 1024,
        "extension": "py",
        "lines": 42
      }
    ]
  },
  "context": {
    "project": {
      "name": "project-name",
      "root": "/project/root",
      "git_branch": "main",
      "git_commit": "abc123"
    },
    "environment": {
      "user": "username",
      "hostname": "host",
      "pwd": "/current/dir",
      "shell": "/bin/bash"
    }
  },
  "ai_metadata": {
    "hint": "Code was modified. Check for syntax errors, logical issues, or improvements.",
    "human_note": "File editing operation",
    "debug_priority": "normal",
    "suggested_action": "Continue monitoring"
  }
}
```

### 2. AI向けメタデータ
- **ai_hint**: AIがログを解析する際のヒント
- **human_note**: 人間による補足説明
- **debug_priority**: デバッグ優先度（high/normal）
- **suggested_action**: 推奨される次のアクション

### 3. 豊富なコンテキスト情報
- プロジェクト情報（名前、ルート、Gitブランチ、コミット）
- 環境情報（ユーザー、ホスト、作業ディレクトリ）
- ファイル情報（パス、サイズ、拡張子、行数）

## 📦 導入方法

### 既存システムとの統合

現在の設定ファイル（`.claude/settings.json`）に以下を追加：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/scripts/ai-logger.sh"
          },
          {
            "type": "command",
            "command": ".claude/scripts/activity-logger.sh"
          }
        ]
      }
    ]
  }
}
```

これにより、既存のログシステムと並行してAIログが生成されます。

## 🔍 ログ解析

### 基本的な使用方法

```bash
# サマリー表示
.claude/scripts/analyze-ai-logs.py

# JSON形式で詳細表示
.claude/scripts/analyze-ai-logs.py --format json

# エラーのみ表示
.claude/scripts/analyze-ai-logs.py --errors-only
```

### 解析レポートの内容

1. **サマリー情報**
   - 総操作数
   - エラー数
   - 操作タイプ別内訳
   - 時間範囲

2. **エラー分析**
   - エラーパターン
   - AIヒント
   - 推奨アクション

3. **パターン検出**
   - 頻繁な操作
   - エラー率の高い操作
   - ファイルアクティビティ

4. **AI洞察**
   - 高エラー率の警告
   - 繰り返し操作の最適化提案

5. **デバッグヒント**
   - エラーコンテキスト
   - AI向け指示
   - 人間の注記

## 🎯 利点

### 開発効率の向上
- **コンテキスト豊富なデバッグ**: AIが問題の根本原因を素早く特定
- **パターン認識**: 繰り返しのエラーや非効率な操作の発見
- **予防的分析**: 問題が大きくなる前に検出

### AI支援の最大化
- **構造化データ**: AIが理解しやすい形式
- **明示的な指示**: human_noteとai_todoフィールド
- **優先度付け**: 重要な問題から対処

### 既存システムとの共存
- 従来のactivity.logも継続生成
- 段階的な移行が可能
- 後方互換性を維持

## 📊 活用例

### デバッグセッション
```bash
# エラーが発生した場合
.claude/scripts/analyze-ai-logs.py --errors-only > debug_report.json

# AIに分析を依頼
"このdebug_report.jsonを分析して、エラーの原因と解決策を提案してください"
```

### パフォーマンス分析
```bash
# 全体の活動パターンを確認
.claude/scripts/analyze-ai-logs.py --format json | jq '.patterns'

# 頻繁に編集されるファイルを特定
.claude/scripts/analyze-ai-logs.py --format json | jq '.patterns.file_activity'
```

### 定期レビュー
```bash
# 週次レポート生成
.claude/scripts/analyze-ai-logs.py > weekly_report.txt

# AIに改善提案を依頼
"このweekly_report.txtを基に、開発プロセスの改善点を提案してください"
```

## 🔧 カスタマイズ

### 新しい操作タイプの追加
`ai-logger.sh`のcase文に追加：
```bash
"NewTool")
    operation_type="NEW_OPERATION"
    ai_hint="New operation detected. Analyze purpose and impact."
    human_note="Custom tool operation"
    ;;
```

### カスタムメタデータ
ログエントリにプロジェクト固有の情報を追加可能

## 📈 今後の拡張

1. **リアルタイムアラート**: エラー率が閾値を超えた場合の通知
2. **視覚化ダッシュボード**: ログデータのグラフ表示
3. **AI自動分析**: 定期的な自動レポート生成
4. **他言語サポート**: TypeScript版の実装

## 🤝 移行戦略

1. **Phase 1**: 既存システムと並行運用（現在）
2. **Phase 2**: AIログの活用度を徐々に増加
3. **Phase 3**: 完全移行（オプション）

このAIログシステムにより、Vibe Codingの概念を実現し、AIとの協調による効率的な開発が可能になります。

## 📚 参考情報・謝辞

### Vibe Logger - 本システムのインスピレーション
- **プロジェクト**: [Vibe Logger](https://github.com/fladdict/vibe-logger) by @fladdict
- **解説記事**: [AIエージェント向けログシステム「Vibe Logger」の提案](https://note.com/fladdict/n/n5046f72bdadd)

### Vibe Loggerから採用した主要概念
1. **構造化ログ形式**: AI解析に最適化されたJSON構造
2. **コンテキスト豊富なメタデータ**: プロジェクト・環境・Git情報の自動収集
3. **AIヒント機構**: デバッグヒント・優先度・推奨アクションの明示化
4. **VibeCoding思想**: 「推測と確認」から「分析と解決」への転換

本システムはVibe Loggerの革新的なアイデアを基に、既存のClaude Codeプロジェクトに統合しやすい形で実装しました。
