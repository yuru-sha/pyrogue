#!/bin/bash

# Claude Code AI-Friendly Activity Logger
# Vibe Logger概念を取り入れたAI最適化ログシステム

# 環境変数から情報を取得
tool_name="${CLAUDE_TOOL_NAME:-unknown}"
file_paths="${CLAUDE_FILE_PATHS:-}"
command="${CLAUDE_COMMAND:-}"
exit_code="${CLAUDE_EXIT_CODE:-0}"
output="${CLAUDE_OUTPUT:-}"
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
correlation_id=$(uuidgen 2>/dev/null || echo "$(date +%s)-$$")

# ログファイルの設定
AI_LOG_FILE="${HOME}/.claude/ai-activity.jsonl"
mkdir -p "$(dirname "$AI_LOG_FILE")"

# プロジェクト情報の取得
project_root="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
project_name=$(basename "$project_root")
git_branch=$(cd "$project_root" && git branch --show-current 2>/dev/null || echo "none")
git_commit=$(cd "$project_root" && git rev-parse --short HEAD 2>/dev/null || echo "none")

# 操作タイプの判定とAIヒントの生成
operation_type="UNKNOWN"
ai_hint=""
human_note=""

case "$tool_name" in
    "Edit"|"Write"|"MultiEdit")
        operation_type="CODE_MODIFICATION"
        ai_hint="Code was modified. Check for syntax errors, logical issues, or improvements."
        human_note="File editing operation"
        ;;
    "Read")
        operation_type="FILE_INSPECTION"
        ai_hint="File was read for analysis. Consider the context and purpose."
        human_note="Information gathering"
        ;;
    "Bash")
        operation_type="COMMAND_EXECUTION"
        ai_hint="Command executed. Check exit code and output for issues."
        human_note="System command: $command"
        ;;
    "Glob"|"Grep")
        operation_type="FILE_SEARCH"
        ai_hint="Search operation performed. Analyze patterns and results."
        human_note="Looking for: ${command:-pattern}"
        ;;
    "Task")
        operation_type="AI_AGENT_TASK"
        ai_hint="Autonomous agent task. Review task completion and results."
        human_note="Agent delegated task"
        ;;
    "TodoWrite")
        operation_type="TASK_MANAGEMENT"
        ai_hint="Task list updated. Check task priorities and dependencies."
        human_note="Project planning activity"
        ;;
    *)
        operation_type="OTHER_OPERATION"
        ai_hint="Unknown operation type. Analyze based on context."
        ;;
esac

# ファイル情報の収集
files_info="[]"
if [ -n "$file_paths" ]; then
    files_info=$(echo "$file_paths" | tr ',' '\n' | while read -r file; do
        if [ -f "$file" ]; then
            size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            ext="${file##*.}"
            lines=$(wc -l < "$file" 2>/dev/null || echo "0")
            echo "{\"path\":\"$file\",\"size\":$size,\"extension\":\"$ext\",\"lines\":$lines}"
        fi
    done | jq -s '.' 2>/dev/null || echo "[]")
fi

# 構造化ログエントリの作成
log_entry=$(jq -n \
    --arg timestamp "$timestamp" \
    --arg correlation_id "$correlation_id" \
    --arg tool "$tool_name" \
    --arg operation_type "$operation_type" \
    --arg project_name "$project_name" \
    --arg project_root "$project_root" \
    --arg git_branch "$git_branch" \
    --arg git_commit "$git_commit" \
    --arg command "$command" \
    --arg exit_code "$exit_code" \
    --arg ai_hint "$ai_hint" \
    --arg human_note "$human_note" \
    --argjson files "$files_info" \
    '{
        "timestamp": $timestamp,
        "correlation_id": $correlation_id,
        "operation": {
            "tool": $tool,
            "type": $operation_type,
            "command": $command,
            "exit_code": ($exit_code | tonumber),
            "files": $files
        },
        "context": {
            "project": {
                "name": $project_name,
                "root": $project_root,
                "git_branch": $git_branch,
                "git_commit": $git_commit
            },
            "environment": {
                "user": env.USER,
                "hostname": env.HOSTNAME,
                "pwd": env.PWD,
                "shell": env.SHELL
            }
        },
        "ai_metadata": {
            "hint": $ai_hint,
            "human_note": $human_note,
            "debug_priority": (if ($exit_code | tonumber) != 0 then "high" else "normal" end),
            "suggested_action": (if ($exit_code | tonumber) != 0 then "Investigate error" else "Continue monitoring" end)
        }
    }' 2>/dev/null)

# JSONLファイルに追記
if [ -n "$log_entry" ]; then
    echo "$log_entry" >> "$AI_LOG_FILE"
fi

# エラー発生時の追加コンテキスト収集
if [ "$exit_code" != "0" ] && [ -n "$output" ]; then
    error_context=$(jq -n \
        --arg timestamp "$timestamp" \
        --arg correlation_id "$correlation_id" \
        --arg output "$output" \
        '{
            "timestamp": $timestamp,
            "correlation_id": $correlation_id,
            "error_details": {
                "output": $output,
                "ai_todo": "Analyze this error output and suggest fixes",
                "context": "Error occurred during operation"
            }
        }' 2>/dev/null)

    if [ -n "$error_context" ]; then
        echo "$error_context" >> "$AI_LOG_FILE"
    fi
fi

# 既存のシンプルログも継続（互換性のため）
echo "[$timestamp] Tool: $tool_name ($operation_type)" >> "${HOME}/.claude/activity.log"

exit 0
