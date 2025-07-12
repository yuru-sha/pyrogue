#!/bin/bash

# Claude Code Security Hook - Deny List Checker
# Blocks potentially dangerous commands while allowing normal development

command=$(cat)
LOG_FILE="${HOME}/.claude/security.log"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

log_attempt() {
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

# Focused list of truly dangerous patterns
DANGEROUS_PATTERNS=(
    # System destruction
    "rm -rf /"
    "rm -rf /[^/]*$"  # rm -rf /usr, /bin, etc.
    "chmod -R 777 /"

    # Remote code execution
    "curl.*\|.*sh"
    "wget.*\|.*bash"

    # Privilege escalation to root shell
    "sudo su"
    "sudo -i"

    # Data destruction
    "dd if=/dev/zero of=/dev/"
    "DROP DATABASE.*;"
    "> /dev/sda"
)

# Check command
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$command" | grep -qE "$pattern"; then
        log_attempt "BLOCKED: $command (matched: $pattern)"
        echo "Security warning: Potentially dangerous command detected"
        echo "Blocked command: $command"
        echo "Matched pattern: $pattern"
        echo ""
        echo "This command is blocked for safety. If needed, consult your administrator."
        exit 1
    fi
done

# Allow and log the command
log_attempt "ALLOWED: $command"
exit 0
