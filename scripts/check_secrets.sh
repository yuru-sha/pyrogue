#!/usr/bin/env bash

set -euo pipefail

# 高信頼な形式だけを検査する。網羅的な秘密情報スキャナの代替にはしない。
readonly SECRET_PATTERN='-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|npm_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{20,}'

paths=("$@")
if ((${#paths[@]} == 0)); then
    while IFS= read -r -d '' path; do
        paths+=("$path")
    done < <(git ls-files --cached --others --exclude-standard -z)
fi

found=0
for path in "${paths[@]}"; do
    [[ -f "$path" && ! -L "$path" ]] || continue
    if grep -E -I -q -- "$SECRET_PATTERN" "$path"; then
        printf 'Potential credential pattern detected in %s\n' "$path" >&2
        found=1
    fi
done

if ((found)); then
    printf 'Secret scan failed; inspect the listed files without printing their values.\n' >&2
    exit 1
fi
