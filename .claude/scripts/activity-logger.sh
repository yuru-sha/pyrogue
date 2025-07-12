#!/bin/bash

# Claude Code Activity Logger Hook
# 開発活動の自動ログ記録

# 環境変数から情報を取得
tool_name="${CLAUDE_TOOL_NAME:-unknown}"
file_paths="${CLAUDE_FILE_PATHS:-}"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# ログファイルの設定
LOG_FILE="${HOME}/.claude/activity.log"
METRICS_FILE="${HOME}/.claude/metrics.log"

# ディレクトリが存在しない場合は作成
mkdir -p "$(dirname "$LOG_FILE")"

# 基本的な活動ログ
echo "[$timestamp] Tool: $tool_name" >> "$LOG_FILE"

# ファイル操作の詳細ログ
if [ -n "$file_paths" ]; then
    IFS=',' read -ra FILES <<< "$file_paths"
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            file_size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            file_ext="${file##*.}"
            echo "[$timestamp] File: $file (${file_size}B, .$file_ext)" >> "$LOG_FILE"
        fi
    done
fi

# 簡単なメトリクス収集
case "$tool_name" in
    "Edit"|"Write"|"MultiEdit")
        echo "[$timestamp] CODE_EDIT" >> "$METRICS_FILE"
        ;;
    "Read")
        echo "[$timestamp] FILE_READ" >> "$METRICS_FILE"
        ;;
    "Bash")
        echo "[$timestamp] COMMAND_EXEC" >> "$METRICS_FILE"
        ;;
    "Glob"|"Grep")
        echo "[$timestamp] FILE_SEARCH" >> "$METRICS_FILE"
        ;;
    *)
        echo "[$timestamp] OTHER_TOOL" >> "$METRICS_FILE"
        ;;
esac

exit 0
