#!/bin/bash

# Claude Code Security Hook - Allow List Checker
# Allows common development commands

command=$(cat)
LOG_FILE="${HOME}/.claude/security.log"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

log_attempt() {
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

# Common development command patterns
ALLOWED_PATTERNS=(
    # File operations
    "^(ls|cat|head|tail|grep|find|mkdir|touch|cp|mv|rm|chmod|chown)( |$)"

    # Git - all common operations
    "^git( |$)"

    # Node.js ecosystem
    "^(npm|yarn|pnpm|npx|node)( |$)"

    # Python ecosystem
    "^(python|python3|pip|pip3|poetry|uv|conda)( |$)"

    # Build tools
    "^(make|cmake|cargo|go|mvn|gradle|docker)( |$)"

    # Text processing
    "^(awk|sed|sort|uniq|wc|cut|tr|jq)( |$)"

    # Modern CLI tools
    "^(eza|batcat|bat|rg|fd|dust|z|fzf)( |$)"

    # System info & monitoring
    "^(ps|top|htop|df|free|uname|whoami|pwd|env|date)( |$)"

    # Network tools (safe operations)
    "^(curl|wget|ping|nslookup|dig)( |$)"

    # Editors
    "^(nano|vim|vi|emacs|code)( |$)"

    # Archive tools
    "^(tar|zip|unzip|gzip|gunzip)( |$)"

    # Other development tools
    "^(ssh|scp|rsync|diff|patch)( |$)"
)

# Check if command is allowed
for pattern in "${ALLOWED_PATTERNS[@]}"; do
    if echo "$command" | grep -qE "$pattern"; then
        log_attempt "ALLOWED: $command"
        exit 0
    fi
done

# Command not in allow list
log_attempt "DENIED: $command (not in allow list)"
echo "Security warning: Command not in allow list"
echo "Denied command: $command"
echo ""
echo "This command is not in the allow list. Contact admin to add it if needed."
exit 1
