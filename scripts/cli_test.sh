#!/usr/bin/env bash

set -euo pipefail

CLI_TEST_SEED="${CLI_TEST_SEED:-20260908}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    printf '%b\n' "${BLUE}[INFO]${NC} $1"
}

log_success() {
    printf '%b\n' "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    printf '%b\n' "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    printf '%b\n' "${RED}[ERROR]${NC} $1"
}

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

run_with_timeout() {
    if command -v timeout >/dev/null 2>&1; then
        timeout 20 "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout 20 "$@"
    elif command -v perl >/dev/null 2>&1; then
        perl -e 'alarm shift; exec @ARGV' 20 "$@"
    else
        log_error "A timeout command (timeout, gtimeout, or perl) is required"
        return 127
    fi
}

run_cli() {
    run_with_timeout make run ARGS="--cli --seed ${CLI_TEST_SEED}"
}

run_cli_with_args() {
    run_with_timeout make run ARGS="--seed ${CLI_TEST_SEED} $1"
}

run_test() {
    local test_name="$1"
    local commands="$2"
    local expected_pattern="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"

    local output
    if output=$(printf '%b\n' "$commands" | run_cli 2>&1); then
        if printf '%s\n' "$output" | grep -E -q -- "$expected_pattern"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
            log_success "$test_name - PASSED"
            TEST_RESULTS+=("PASSED: $test_name")
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
            log_error "$test_name - FAILED (pattern not found: $expected_pattern)"
            TEST_RESULTS+=("FAILED: $test_name")
            printf '%s\n' "$output" | tail -n 20
        fi
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "$test_name - FAILED (command execution failed)"
        TEST_RESULTS+=("FAILED: $test_name")
        printf '%s\n' "$output" | tail -n 20
    fi
}

run_test_with_args() {
    local test_name="$1"
    local args="$2"
    local expected_pattern="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"

    local output
    if output=$(run_cli_with_args "$args" 2>&1); then
        if printf '%s\n' "$output" | grep -E -q -- "$expected_pattern"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
            log_success "$test_name - PASSED"
            TEST_RESULTS+=("PASSED: $test_name")
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
            log_error "$test_name - FAILED (pattern not found: $expected_pattern)"
            TEST_RESULTS+=("FAILED: $test_name")
            printf '%s\n' "$output" | tail -n 20
        fi
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "$test_name - FAILED (command execution failed)"
        TEST_RESULTS+=("FAILED: $test_name")
        printf '%s\n' "$output" | tail -n 20
    fi
}

run_determinism_test() {
    local test_name="同一seedのCLI出力再現性"
    local first_output
    local second_output

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"
    first_output=$(printf 'status\nquit\n' | run_cli 2>&1)
    second_output=$(printf 'status\nquit\n' | run_cli 2>&1)
    if [[ "$first_output" == "$second_output" ]]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "$test_name - PASSED"
        TEST_RESULTS+=("PASSED: $test_name")
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "$test_name - FAILED"
        TEST_RESULTS+=("FAILED: $test_name")
    fi
}

main() {
    if [[ ! "$CLI_TEST_SEED" =~ ^-?[0-9]+$ ]]; then
        log_error "CLI_TEST_SEED must be an integer"
        exit 2
    fi

    log_info "PyRogue canonical CLI smoke tests (seed=${CLI_TEST_SEED})"
    run_test_with_args "ヘルプ表示" "--help" "PyRogue - A Python Roguelike Game"
    run_test "CLI終了" "quit" "Goodbye\."
    run_test "ヘルプコマンド" "help\nquit" "hjkl yubn move"
    run_test "ステータス表示" "status\nquit" "Level 1  HP"
    run_test "インベントリ表示" "inventory\nquit" "mace"
    run_test "待機コマンド" "wait\nquit" "You wait\."
    run_test "不正な移動方向" "move invalid\nquit" "Invalid direction\."
    run_test "アミュレットなしの脱出拒否" "stairs up\nquit" "need the Amulet of Yendor"
    run_determinism_test

    echo ""
    echo "Tests: ${PASSED_TESTS}/${TOTAL_TESTS} passed"
    for result in "${TEST_RESULTS[@]}"; do
        echo "  $result"
    done

    if ((FAILED_TESTS > 0)); then
        log_error "CLI smoke tests failed"
        exit 1
    fi
    log_success "All CLI smoke tests passed"
}

main "$@"
