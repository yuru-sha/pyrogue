#!/bin/bash

# PyRogue CLIモード自動テストスクリプト
#
# このスクリプトは、PyRogueのCLIモードで基本的な動作確認を自動化します。
# リファクタリング後の動作確認や回帰テストに使用できます。

set -e  # エラー時に終了

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# テスト結果管理
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

# テスト実行関数
run_test() {
    local test_name="$1"
    local commands="$2"
    local expected_pattern="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"

    # コマンド実行
    local output
    if output=$(echo -e "$commands" | timeout 10 make run ARGS="--cli" 2>&1); then
        # 期待される文字列が含まれているかチェック
        if echo "$output" | grep -q "$expected_pattern"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
            log_success "✅ $test_name - PASSED"
            TEST_RESULTS+=("✅ $test_name - PASSED")
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
            log_error "❌ $test_name - FAILED (Pattern not found: $expected_pattern)"
            TEST_RESULTS+=("❌ $test_name - FAILED")
            echo "Output: $output"
        fi
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "❌ $test_name - FAILED (Command execution failed)"
        TEST_RESULTS+=("❌ $test_name - FAILED")
        echo "Output: $output"
    fi

    echo ""
}

# テスト実行関数（コマンドライン引数版）
run_test_with_args() {
    local test_name="$1"
    local args="$2"
    local expected_pattern="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"

    # コマンド実行
    local output
    if output=$(timeout 10 make run ARGS="$args" 2>&1); then
        # 期待される文字列が含まれているかチェック
        if echo "$output" | grep -q "$expected_pattern"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
            log_success "✅ $test_name - PASSED"
            TEST_RESULTS+=("✅ $test_name - PASSED")
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
            log_error "❌ $test_name - FAILED (Pattern not found: $expected_pattern)"
            TEST_RESULTS+=("❌ $test_name - FAILED")
            echo "Output: $output"
        fi
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "❌ $test_name - FAILED (Command execution failed)"
        TEST_RESULTS+=("❌ $test_name - FAILED")
        echo "Output: $output"
    fi

    echo ""
}

# メイン実行部
main() {
    log_info "PyRogue CLIモード自動テスト開始"
    echo "================================================================"
    echo ""

    # 1. 基本起動テスト
    log_info "=== 基本起動テスト ==="
    run_test_with_args "ヘルプ表示テスト" "--help" "PyRogue - A Python Roguelike Game"
    run_test "CLIモード起動テスト" "quit" "PyRogue CLI Mode"

    # 2. 基本コマンドテスト
    log_info "=== 基本コマンドテスト ==="
    run_test "ヘルプコマンドテスト" "help\nquit" "Available Commands"
    run_test "ステータス表示テスト" "status\nquit" "PLAYER STATUS"
    run_test "周辺確認テスト" "look\nquit" "Floor: B1F"

    # 3. 移動システムテスト
    log_info "=== 移動システムテスト ==="
    run_test "基本移動テスト" "n\nquit" "Floor: B1F"
    run_test "移動制限テスト" "n\nn\nn\nn\nn\nquit" "Player:"

    # 4. インベントリシステムテスト
    log_info "=== インベントリシステムテスト ==="
    run_test "インベントリ表示テスト" "inventory\nquit" "INVENTORY"
    run_test "初期装備確認テスト" "inventory\nquit" "Dagger.*equipped"

    # 5. ゲームオーバーテスト
    log_info "=== ゲームオーバーテスト ==="
    run_test "HP直接設定死亡テスト" "status\ndebug hp 0\nquit" "You have died"
    run_test "ダメージによる死亡テスト" "status\ndebug damage 999\nquit" "You have died"
    run_test "段階的ダメージテスト" "status\ndebug damage 10\nstatus\ndebug damage 5\nstatus\nquit" "HP: 5/20"
    run_test "ゲームオーバー表示テスト" "debug hp 0\nquit" "GAME OVER"

    # 6. イェンダーのアミュレットテスト
    log_info "=== イェンダーのアミュレットテスト ==="
    run_test "アミュレットデバッグ取得テスト" "debug yendor\nquit" "You now possess the Amulet of Yendor"
    run_test "アミュレット効果確認テスト" "debug yendor\nstatus\nquit" "Has Amulet: Yes"
    run_test "脱出階段生成テスト" "debug yendor\ndebug floor 1\nlook\nquit" "Floor: B1F"
    run_test "勝利条件テスト" "debug yendor\nstairs up\nquit" "You have escaped with the Amulet of Yendor"
    run_test "階層テレポートテスト" "debug floor 26\nstatus\ndebug floor 1\nstatus\nquit" "Floor: B1F"

    # 6. 統合動作テスト
    log_info "=== 統合動作テスト ==="
    run_test "複合操作テスト" "help\nstatus\ninventory\nlook\nn\ne\nstatus\nquit" "PLAYER STATUS"

    # テスト結果サマリー
    echo "================================================================"
    log_info "テスト結果サマリー"
    echo "================================================================"

    echo ""
    echo "📊 テスト統計:"
    echo "  総テスト数: $TOTAL_TESTS"
    echo -e "  成功: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "  失敗: ${RED}$FAILED_TESTS${NC}"
    echo ""

    echo "📋 詳細結果:"
    for result in "${TEST_RESULTS[@]}"; do
        echo "  $result"
    done
    echo ""

    # 成功率計算
    if [ $TOTAL_TESTS -gt 0 ]; then
        local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
        if [ $success_rate -eq 100 ]; then
            log_success "🎉 全テスト成功! 成功率: ${success_rate}%"
        elif [ $success_rate -ge 80 ]; then
            log_warning "⚠️  テスト成功率: ${success_rate}% (一部失敗)"
        else
            log_error "❌ テスト成功率: ${success_rate}% (多数失敗)"
        fi
    else
        log_warning "テストが実行されませんでした"
    fi

    echo ""

    # 終了コード設定
    if [ $FAILED_TESTS -gt 0 ]; then
        log_error "一部のテストが失敗しました"
        exit 1
    else
        log_success "すべてのテストが成功しました"
        exit 0
    fi
}

# スクリプト実行
main "$@"
