---
cache_control: {"type": "ephemeral"}
---
# PyRogue - 機能一覧

## 概要

PyRogueは、伝統的なローグライクゲームの要素を現代的な技術で実装した完全なゲームシステムです。以下では、実装されている機能を詳細に説明します。

## ゲームプレイ機能

### 1. ダンジョン探索システム

#### BSPダンジョン生成システム
- **26階層のダンジョン**: オリジナルRogueに準拠した階層構造
- **BSP（Binary Space Partitioning）**: RogueBasinチュートリアル準拠の手続き生成
- **部屋とコリドーシステム**: 部屋中心間をL字型通路で接続
- **階段システム**: 上り/下り階段による階層移動
- **⭐迷路階層システム**: 7階、13階、19階は迷路生成

#### BSP生成の特徴
- **再帰的空間分割**: BSPアルゴリズムによる自然な部屋配置
- **接続保証**: 全部屋が必ず接続される設計
- **中心間接続**: 部屋の境界ではなく中心同士を接続
- **適応的サイズ**: ノードサイズに応じた適切な部屋生成

#### 高度なドア配置システム
- **部屋境界突破判定**: 通路が部屋の外周を突き抜ける箇所のみでドア配置
- **連続ドア防止**: 隣接8方向の重複ドア配置を自動回避
- **ランダム状態**: 60%クローズド、30%オープン、10%隠し扉
- **戦術的配置**: 回避困難で戦術的価値の高い位置にのみ配置

#### 実装場所
- `src/pyrogue/map/dungeon/section_based_builder.py` - BSPダンジョン生成
- `src/pyrogue/map/dungeon/maze_builder.py` - 迷路生成専用ビルダー
- `src/pyrogue/map/dungeon/director.py` - ダンジョン生成ディレクター
- `src/pyrogue/map/dungeon_manager.py` - マルチフロア管理

#### 詳細仕様
```python
# BSPダンジョン生成パラメータ
DUNGEON_DEPTH = 26                    # 最大階層数
MIN_SIZE = 5                          # BSPノード最小サイズ（RogueBasin準拠）
ROOM_MIN_SIZE = 3                     # 最小部屋サイズ
L_SHAPED_CORRIDORS = True             # L字型通路接続

# ドア配置パラメータ
DOOR_CLOSED_RATE = 0.6                # クローズドドア確率
DOOR_OPEN_RATE = 0.3                  # オープンドア確率
DOOR_SECRET_RATE = 0.1                # 隠し扉確率
ADJACENT_DOOR_PREVENTION = True       # 連続ドア防止

# 迷路階層パラメータ
MAZE_GUARANTEED_FLOORS = [7, 13, 19]  # 必ず迷路になる階層
MAZE_COMPLEXITY = 0.75                # 迷路の複雑さ
```

### 2. 移動・操作システム

#### 基本移動
- **Vi-keys**: hjkl + 対角線移動 (yubn)
- **矢印キー**: 標準的な方向移動
- **テンキー**: 1-9による移動（対角線含む）

#### 操作アクション
- **g**: アイテムの取得
- **o**: 扉を開く
- **c**: 扉を閉じる
- **s**: 隠し扉・トラップの探索
- **d**: トラップの解除
- **Tab**: 視界（FOV）表示の切り替え
- **i**: インベントリ画面
- **z**: 魔法書（spellbook）

#### 実装場所
- `src/pyrogue/core/input_handlers.py` - 入力処理
- `src/pyrogue/ui/components/input_handler.py` - UI入力処理
- `src/pyrogue/core/command_handler.py` - 統一コマンド処理

#### コマンド統一化システム
- **共通コマンドハンドラー**: GUIとCLIで統一されたコマンド処理
- **コマンド抽象化**: インターフェース層での統一的な操作
- **キー入力変換**: GUI環境でのキー→コマンド自動変換

### 3. トラップシステム

#### 探索・解除システム
- **安全な探索**: `s`キーで隣接8方向の隠しトラップを探索
- **安全な解除**: `d`キーで隣接8方向の発見済みトラップを解除
- **レベル依存成功率**: プレイヤーレベルに応じた発見・解除成功率
- **踏まずに処理**: トラップに触れることなく安全に対処

#### トラップタイプ
- **落とし穴トラップ**: 固定ダメージ（茶色の`P`で表示）
- **毒針トラップ**: 毒状態異常（緑色の`N`で表示）
- **テレポートトラップ**: ランダムテレポート（マゼンタの`T`で表示）

#### 実装場所
- `src/pyrogue/entities/traps/trap.py` - トラップ基底クラス・各種トラップ
- `src/pyrogue/core/game_logic.py` - 探索・解除ロジック（`search_trap`, `disarm_trap`）

#### 詳細仕様
```python
# トラップ探索・解除パラメータ
TRAP_SEARCH_BASE_RATE = 40            # 基本発見成功率（%）
TRAP_SEARCH_LEVEL_BONUS = 5           # レベルボーナス（%/level）
TRAP_SEARCH_MAX_RATE = 90             # 最大発見成功率（%）
TRAP_DISARM_BASE_RATE = 70            # 基本解除成功率（%）
TRAP_DISARM_FAILURE_TRIGGER = 30      # 解除失敗時の発動確率（%）
```

### 4. ウィザードモード（デバッグシステム）

#### 基本機能
- **Ctrl+W**: ウィザードモード切り替え
- **環境変数連携**: `DEBUG=true`で自動有効化
- **開発支援**: トラップ・ダンジョン生成・バランステスト用

#### 可視化機能
- **全マップ表示**: FOV無視で全ダンジョン表示
- **隠し扉表示**: 紫色の`S`で未発見隠しドアを表示
- **トラップ表示**: タイプ別色分け（隠しトラップは薄い色）
- **全エンティティ表示**: アイテム・モンスター・NPCを常時表示

#### 無敵モード
- **トラップ無効化**: トラップを踏んでも発動しない
- **ダメージ無効化**: モンスター攻撃でダメージを受けない
- **警告メッセージ**: `[Wizard]`プレフィックスで通知

#### 操作機能
- **Ctrl+T**: 階段位置にテレポート
- **Ctrl+U**: レベルアップ（HP/MP増加）
- **Ctrl+H**: 完全回復（HP/MP全回復）
- **Ctrl+R**: 全マップ探索（全隠し要素発見）

#### 実装場所
- `src/pyrogue/core/game_logic.py` - ウィザードモード管理
- `src/pyrogue/ui/components/game_renderer.py` - 可視化機能
- `src/pyrogue/ui/components/input_handler.py` - ウィザードコマンド

### 5. 戦闘システム

#### 基本戦闘
- **ターンベース**: プレイヤー → モンスター → 環境効果
- **近接戦闘**: 隣接するモンスターへの攻撃
- **ダメージ計算**: 攻撃力 - 防御力（最低1ダメージ保証）
- **クリティカルヒット**: 5%確率で2倍ダメージ

#### 実装場所
- `src/pyrogue/core/managers/combat_manager.py` - 戦闘管理
- `src/pyrogue/core/managers/turn_manager.py` - ターン管理

#### 詳細仕様
```python
# 戦闘パラメータ
CRITICAL_HIT_CHANCE = 0.05            # クリティカルヒット確率
CRITICAL_HIT_MULTIPLIER = 2.0         # クリティカルヒット倍率
MIN_DAMAGE = 1                        # 最低ダメージ
BASE_ATTACK_BONUS = 1                 # 基本攻撃ボーナス
```

### 4. 経験値・レベルシステム

#### 成長システム
- **経験値獲得**: モンスター撃破時に獲得
- **レベル差補正**: レベル差による経験値調整
- **能力値成長**: レベルアップ時のHP/MP増加

#### 実装場所
- `src/pyrogue/entities/actors/player.py` - プレイヤー成長
- `src/pyrogue/core/managers/combat_manager.py` - 経験値計算

#### 詳細仕様
```python
# 経験値システム
XP_PER_LEVEL = 100                    # レベルアップ必要経験値
HP_PER_LEVEL = 10                     # レベルアップ時HP増加
MP_PER_LEVEL = 5                      # レベルアップ時MP増加
```

## 新機能システム

### 1. NPCシステム（現在無効化中）

**注意**: NPCシステムは完全に実装済みですが、現在は無効化されています。将来の拡張機能として残されています。

#### 基本機能
- **商人NPC**: アイテムの売買システム
- **会話システム**: 対話による情報交換
- **取引システム**: 経済活動の実装
- **ダンジョン配置**: 特別な部屋への自動配置

#### NPC種類
- **商人 (Merchant)**: アイテム売買、価格交渉
- **警備員 (Guard)**: 情報提供、安全保障
- **村人 (Villager)**: 一般的な対話、噂話
- **僧侶 (Priest)**: 回復・浄化サービス、祝福
- **魔術師 (Mage)**: 魔法関連サービス、呪文販売

#### 実装場所
- `src/pyrogue/entities/actors/npc.py` - NPC基底クラス
- `src/pyrogue/core/managers/dialogue_manager.py` - 会話管理
- `src/pyrogue/core/managers/trading_manager.py` - 取引管理
- `src/pyrogue/ui/screens/dialogue_screen.py` - 会話UI
- `src/pyrogue/ui/screens/trading_screen.py` - 取引UI

#### 無効化の制御
```python
# constants.py - FeatureConstants
ENABLE_NPC_SYSTEM: bool = False       # NPCシステムを無効化
ENABLE_DIALOGUE: bool = False         # 対話システムを無効化
ENABLE_TRADING: bool = False          # 取引システムを無効化
```

#### 詳細仕様
```python
# NPC配置パラメータ
NPC_SPAWN_RATE = 0.3                  # NPC出現確率
MERCHANT_MARKUP = 1.5                 # 商人マークアップ倍率
TRADE_DISCOUNT = 0.7                  # 買取価格割引率
```

### 2. 多様なモンスターAI

#### AI行動パターン
- **追跡AI**: プレイヤーの追跡・攻撃
- **逃走AI**: HP低下時の逃走行動
- **遠距離攻撃AI**: 射程攻撃の実行
- **特殊攻撃AI**: アイテム盗取・レベル下げ
- **分裂AI**: ダメージ時の分裂行動

#### 特殊能力
- **アイテム盗取**: インベントリからランダム盗取（Leprechaun系）
- **ゴールド盗取**: 所持金の窃取（Nymph系）
- **レベル下げ**: プレイヤーレベルの減少（Wraith系）
- **分裂**: HP減少時の個体分裂（Slime系）
- **幻覚攻撃**: 視覚混乱の発症（Dream Eater系）

#### 実装場所
- `src/pyrogue/core/managers/monster_ai_manager.py` - AI管理システム
- `src/pyrogue/entities/actors/monster.py` - モンスター基底クラス

#### 詳細仕様
```python
# モンスターAIパラメータ
ITEM_STEAL_CHANCE = 0.2               # アイテム盗取確率
GOLD_STEAL_RATE = 0.1                 # ゴールド盗取率
LEVEL_DRAIN_CHANCE = 0.15             # レベル下げ確率
SPLIT_HP_THRESHOLD = 0.3              # 分裂発動HP閾値
HALLUCINATION_CHANCE = 0.3            # 幻覚発症確率
```

### 3. 幻覚システム

#### 機能
- **視覚混乱**: モンスターやアイテムの表示をランダム化
- **持続時間**: 8ターンの継続効果
- **状態異常**: 他の状態異常との併用可能
- **視覚効果**: 現実感の喪失メッセージ

#### 幻覚発症条件
- **幻覚ポーション**: 直接摂取による発症
- **モンスター攻撃**: Dream Eater、Phantom Fungusの攻撃
- **特殊トラップ**: 精神攻撃トラップ（将来実装）

#### 実装場所
- `src/pyrogue/entities/actors/status_effects.py` - 状態異常システム
- `src/pyrogue/ui/components/game_renderer.py` - 表示変換
- `src/pyrogue/entities/items/effects.py` - 幻覚ポーション効果

#### 詳細仕様
```python
# 幻覚システムパラメータ
HALLUCINATION_DURATION = 8            # 幻覚持続時間
HALLUCINATION_CHARS = "!@#$%^&*"     # 幻覚時表示文字
HALLUCINATION_COLORS = [              # 幻覚時色彩
    "red", "green", "blue", "yellow", "magenta", "cyan"
]
```

### 4. 強化された飢餓システム

#### 飢餓レベル
- **満腹 (Full)**: 100-80% - HP・MP自然回復ボーナス
- **普通 (Normal)**: 79-40% - ペナルティなし
- **空腹 (Hungry)**: 39-20% - 軽微なペナルティ
- **飢餓 (Starving)**: 19-5% - 重大なペナルティ
- **餓死寸前 (Dying)**: 4-0% - 極度のペナルティ・継続ダメージ

#### ペナルティ効果
- **攻撃力減少**: 飢餓レベルに応じた戦闘力低下
- **防御力減少**: 防御能力の低下
- **移動制限**: 極度の飢餓時の行動制限
- **継続ダメージ**: 餓死寸前時の体力減少

#### 実装場所
- `src/pyrogue/entities/actors/player.py` - プレイヤー飢餓管理
- `src/pyrogue/constants.py` - 飢餓関連定数

#### 詳細仕様
```python
# 飢餓システムパラメータ
HUNGER_DECAY_RATE = 8                 # 飢餓進行ターン数
STARVATION_DAMAGE = 5                 # 餓死ダメージ
HUNGER_ATTACK_PENALTY = 0.5           # 飢餓時攻撃力減少率
HUNGER_DEFENSE_PENALTY = 0.3          # 飢餓時防御力減少率
FULL_RECOVERY_RATE = 0.1              # 満腹時回復率
```

### 5. 完全なアイテム識別システム

#### 機能
- **未識別表示**: オリジナルRogue風の表示
- **識別プロセス**: 使用による自動識別
- **識別の巻物**: 強制識別アイテム
- **同種識別**: 同じアイテムの一括識別

#### 未識別名生成
- **ポーション**: 色による識別（red potion、blue potion等）
- **巻物**: 呪文による識別（scroll labeled "ZELGO MER"等）
- **指輪**: 材質による識別（wooden ring、silver ring等）
- **ランダム化**: プレイ毎に異なる割り当て

#### 実装場所
- `src/pyrogue/entities/items/identification.py` - 識別システム
- `src/pyrogue/entities/actors/player.py` - プレイヤー識別記録

#### 詳細仕様
```python
# 識別システムパラメータ
POTION_COLORS = [                     # ポーション色リスト
    "red", "blue", "green", "yellow", "purple", "orange"
]
SCROLL_LABELS = [                     # 巻物呪文リスト
    "ZELGO MER", "JUYED AWK", "NR 9", "XIXAXA XOXAXA"
]
RING_MATERIALS = [                    # 指輪材質リスト
    "wooden", "silver", "gold", "platinum", "copper"
]
```

### 6. スコアランキングシステム

#### 機能
- **成績記録**: 詳細な統計情報の保存
- **ランキング表示**: 上位100位までの記録
- **死亡原因記録**: 詳細な終了理由の保存
- **勝利判定**: 勝利・敗北の区別

#### 記録項目
- **プレイヤー名**: 記録者名
- **スコア**: 総合評価点（金貨×10 + 経験値×5 + レベル×100 + 撃破×50 + 階層×200）
- **レベル**: 到達レベル
- **最深階**: 到達階層
- **ゴールド**: 所持金
- **撃破数**: モンスター撃破数
- **ターン数**: 総プレイターン数
- **結果**: 勝利/死亡
- **死亡原因**: 詳細な終了理由
- **日時**: 記録日時

#### 実装場所
- `src/pyrogue/core/score_manager.py` - スコア管理システム
- `src/pyrogue/ui/screens/score_screen.py` - スコア表示UI

#### 詳細仕様
```python
# スコア計算パラメータ
SCORE_GOLD_MULTIPLIER = 10            # 金貨スコア倍率
SCORE_XP_MULTIPLIER = 5               # 経験値スコア倍率
SCORE_LEVEL_MULTIPLIER = 100          # レベルスコア倍率
SCORE_KILLS_MULTIPLIER = 50           # 撃破スコア倍率
SCORE_FLOOR_MULTIPLIER = 200          # 階層スコア倍率
```

### 7. 完全なPermadeathシステム

#### 機能
- **セーブファイル削除**: 死亡時の自動削除
- **復活不可**: 真の一回限りのゲーム体験
- **改竄防止**: チェックサム検証による不正防止
- **バックアップ復旧**: 破損時の自動復旧

#### セキュリティ機能
- **SHA256チェックサム**: ファイル整合性の検証
- **暗号化**: セーブデータの暗号化保護
- **改竄検出**: 不正な変更の検出・拒否
- **バックアップ管理**: 自動バックアップ・復旧

#### 実装場所
- `src/pyrogue/core/save_manager.py` - セーブ管理・Permadeath処理
- `src/pyrogue/core/engine.py` - エンジン制御

#### 詳細仕様
```python
# Permadeathシステムパラメータ
SAVE_FILE_PATH = "saves/pyrogue_save.json"
BACKUP_FILE_PATH = "saves/pyrogue_save_backup.json"
CHECKSUM_VERIFICATION = True          # チェックサム検証の有効化
AUTO_BACKUP_INTERVAL = 10             # 自動バックアップ間隔（ターン）
```

## アイテムシステム

### 1. アイテムカテゴリ

#### 武器 (Weapons)
- **近接武器**: 剣、斧、槍など
- **攻撃力ボーナス**: 基本攻撃力への追加
- **装備システム**: 1つの武器のみ装備可能

#### 防具 (Armor)
- **防御力ボーナス**: 基本防御力への追加
- **重量システム**: 防具の重さによる移動制限
- **装備システム**: 1つの防具のみ装備可能

#### 指輪 (Rings)
- **特殊効果**: 攻撃力、防御力、HP回復など
- **複数装備**: 同時に複数装備可能
- **持続効果**: 装備中は常に効果が適用

#### 消耗品 (Consumables)
- **ポーション**: HP回復、毒回復、能力向上
- **巻物**: 魔法効果、識別、テレポート
- **食料**: 満腹度回復、栄養補給

#### 実装場所
- `src/pyrogue/entities/items/item.py` - アイテム基底クラス
- `src/pyrogue/entities/items/item_types.py` - アイテム種別定義
- `src/pyrogue/entities/items/effects.py` - アイテム効果

### 2. インベントリシステム

#### 管理機能
- **26文字制限**: a-zの文字によるアイテム管理
- **装備管理**: 武器、防具、指輪の装備状態管理
- **重量制限**: 運搬可能重量の制限
- **ソート機能**: アイテムの種類別ソート
- **スタック機能**: 同種アイテムの数量管理（ポーション、巻物、食料等）

#### スタック可能アイテム
- **ポーション類**: Potion of Healing等の薬品
- **巻物類**: Scroll of Light等の魔法巻物
- **食料類**: Food Ration等の食品
- **金貨**: Gold pieces（自動スタック）

#### スタック機能の仕様
- **自動統合**: 同名同種アイテムが自動的に統合される
- **数量表示**: スタック数が2個以上の場合 "(x3)" 形式で表示
- **個別使用**: USE操作で1個ずつ消費、残数を正確に管理
- **全体ドロップ**: DROP操作で全スタックを一括ドロップ
- **2025-07-13バグ修正**: USE時の誤削除問題とDROP時の部分残存問題を解決

#### 操作機能
- **i**: インベントリ画面を開く
- **装備/解除**: 装備可能アイテムの着脱
- **使用**: 消耗品の使用（スタック対応、1個ずつ消費）
- **投棄**: 不要なアイテムの投棄（スタック対応、全体ドロップ）
- **?**: インベントリ画面内でヘルプ表示切り替え（JIS配列対応）

#### 実装場所
- `src/pyrogue/entities/actors/inventory.py` - インベントリ管理
- `src/pyrogue/ui/screens/inventory_screen.py` - インベントリUI

## 魔法システム

### 1. 魔法の種類

#### 攻撃魔法
- **Magic Missile**: 必中の魔法攻撃
- **Poison Bolt**: 毒状態を付与する攻撃魔法

#### 回復魔法
- **Heal**: HP回復魔法
- **Cure Poison**: 毒状態の回復

#### 実装場所
- `src/pyrogue/entities/magic/spells.py` - 魔法システム
- `src/pyrogue/ui/screens/magic_screen.py` - 魔法UI

### 2. 魔法書（Spellbook）システム

#### 管理機能
- **魔法の習得**: 新しい魔法の学習
- **MP管理**: 魔法ポイントの消費と回復
- **詠唱システム**: 魔法の発動処理

#### 操作機能
- **z**: 魔法書を開く
- **矢印キー**: 魔法選択
- **Enter**: 魔法の詠唱
- **a-z**: 魔法の直接選択

#### 詳細仕様
```python
# 魔法システム
MP_RECOVERY_RATE = 0.1                # MP自然回復率
MAGIC_MISSILE_COST = 3                # Magic Missile消費MP
HEAL_COST = 5                         # Heal消費MP
CURE_POISON_COST = 4                  # Cure Poison消費MP
POISON_BOLT_COST = 4                  # Poison Bolt消費MP
```

### 4. ゴールドオートピックアップシステム

#### 機能
- **自動回収**: 移動時にゴールドを自動的に回収
- **メッセージ表示**: 回収時の適切な通知表示
- **パフォーマンス最適化**: 効率的なゴールド検出と処理
- **CLIテスト対応**: 統合テストでの動作確認済み

#### 動作仕様
- **発動タイミング**: プレイヤーの移動完了時
- **対象**: プレイヤーと同じ位置にあるゴールドアイテム
- **処理順序**: 移動 → ゴールド回収 → 他アイテム通知 → トラップチェック

#### 実装場所
- `src/pyrogue/core/managers/movement_manager.py` - 移動時の自動回収処理
- `src/pyrogue/entities/items/item.py` - ゴールドアイテム定義

#### 詳細仕様
```python
# ゴールドオートピックアップ処理（MovementManager._check_item_pickup）
gold_items = [
    item
    for item in items_at_position
    if hasattr(item, "item_type") and item.item_type == "GOLD"
]
for gold_item in gold_items:
    amount = getattr(gold_item, "amount", 1)
    player.gold += amount
    floor_data.items.remove(gold_item)
    self.context.add_message(f"You picked up {amount} gold.")
```

#### メッセージ例
```
You picked up 50 gold.
You picked up 25 gold.
```

## 状態異常システム

### 1. 状態異常の種類

#### 毒 (Poison)
- **効果**: 毎ターン継続ダメージ
- **回復**: 時間経過または魔法・アイテムによる回復
- **視覚効果**: 画面表示での状態通知

#### 麻痺 (Paralysis)
- **効果**: 一定ターン行動不能
- **回復**: 時間経過による自動回復
- **戦術的影響**: 戦闘での大きなデメリット

#### 混乱 (Confusion)
- **効果**: 移動方向のランダム化
- **回復**: 時間経過による自動回復
- **戦術的影響**: 意図しない移動による危険

#### 実装場所
- `src/pyrogue/entities/actors/status_effects.py` - 状態異常システム

### 2. 状態異常管理

#### 管理機能
- **複数同時適用**: 異なる状態異常の同時発生
- **持続時間管理**: 各状態異常の残り時間追跡
- **効果の累積**: 同じ状態異常の重複処理

#### 詳細仕様
```python
# 状態異常パラメータ
POISON_DAMAGE = 2                     # 毒ダメージ量
POISON_DURATION = 10                  # 毒持続時間
PARALYSIS_DURATION = 3                # 麻痺持続時間
CONFUSION_DURATION = 5                # 混乱持続時間
```

## トラップシステム

### 1. トラップの種類

#### 落とし穴 (Pit Trap)
- **効果**: 落下ダメージ
- **発見**: 探索コマンドで発見可能
- **回避**: 発見後は回避可能

#### 毒針 (Poison Needle Trap)
- **効果**: 毒状態の付与
- **発見**: 探索コマンドで発見可能
- **解除**: 解除コマンドで無効化可能

#### テレポート (Teleport Trap)
- **効果**: ランダムな場所への移動
- **発見**: 探索コマンドで発見可能
- **回避**: 発見後は回避可能

#### 実装場所
- `src/pyrogue/entities/traps/trap.py` - トラップシステム

### 2. トラップ管理

#### 配置システム
- **確率的配置**: 各フロアでの確率的なトラップ配置
- **隠匿システム**: 初期状態では隠されている
- **発見システム**: 探索コマンドによる発見

#### 詳細仕様
```python
# トラップパラメータ
TRAP_SPAWN_CHANCE = 0.05              # トラップ出現確率
PIT_TRAP_DAMAGE = 10                  # 落とし穴ダメージ
DISARM_SUCCESS_RATE = 0.7             # 解除成功率
SEARCH_SUCCESS_RATE = 0.6             # 探索成功率
```

## UIシステム

### 1. 画面システム

#### メイン画面
- **ゲーム表示**: マップ、キャラクター、アイテムの表示
- **ステータス表示**: HP、MP、レベル、経験値
- **メッセージ表示**: ゲームイベントのメッセージ

#### メニュー画面
- **New Game**: 新しいゲームの開始
- **Load Game**: セーブデータの読み込み
- **Exit**: ゲーム終了

#### 実装場所
- `src/pyrogue/ui/screens/` - 各種画面システム
- `src/pyrogue/ui/components/` - UI コンポーネント

### 2. 視界システム (FOV)

#### 機能
- **視界計算**: プレイヤーの視界範囲計算
- **光源システム**: 光源による視界の変化
- **霧システム**: 未探索・既探索領域の区別

#### 実装場所
- `src/pyrogue/ui/components/fov_manager.py` - 視界管理

## セーブ・ロードシステム

### 1. セーブ機能

#### 保存データ
- **プレイヤー状態**: HP、MP、レベル、装備、インベントリ
- **ダンジョン状態**: 各フロアの状態、モンスター位置
- **ゲーム進行**: 現在フロア、ゲーム時間、スコア

#### 操作
- **Ctrl+S**: 現在の状態をセーブ
- **自動セーブ**: 重要なイベント時の自動保存

#### 実装場所
- `src/pyrogue/core/save_manager.py` - セーブ・ロード管理
- `src/pyrogue/ui/components/save_load_manager.py` - UI連携

### 2. ロード機能

#### 復元データ
- **完全復元**: セーブ時点の状態を完全に復元
- **整合性チェック**: データの整合性確認
- **エラーハンドリング**: 破損データの適切な処理

#### 操作
- **Ctrl+L**: セーブデータの読み込み
- **メニューから選択**: メイン画面からのロード

## モンスターシステム

### 1. AI システム

#### 行動パターン
- **追跡**: プレイヤーの位置に向かって移動
- **攻撃**: 隣接時の攻撃行動
- **待機**: 発見前の待機状態

#### 実装場所
- `src/pyrogue/core/managers/monster_ai_manager.py` - モンスターAI管理
- `src/pyrogue/entities/actors/monster.py` - モンスター基底クラス

### 2. モンスター種別

#### 基本モンスター
- **多様な種類**: A-Zの文字で表現される26種類
- **能力値**: 各モンスター固有の HP、攻撃力、防御力
- **特殊能力**: 一部モンスターの特殊攻撃

#### 実装場所
- `src/pyrogue/entities/actors/monster_types.py` - モンスター定義
- `src/pyrogue/entities/actors/monster_spawner.py` - モンスター生成

## 設定・カスタマイズ

### 1. ゲーム設定

#### パラメータ調整
- **難易度設定**: モンスター出現率、ダメージ倍率
- **表示設定**: 色彩、フォントサイズ
- **操作設定**: キーバインドのカスタマイズ

#### 実装場所
- `src/pyrogue/config.py` - 設定管理（非推奨）
- `src/pyrogue/constants.py` - 定数管理（推奨）

### 2. デバッグ機能

#### 開発支援
- **デバッグモード**: 詳細情報の表示
- **チート機能**: 無敵モード、アイテム生成
- **ログ出力**: 詳細なゲーム状態ログ

#### 実装場所
- `src/pyrogue/utils/logger.py` - ログシステム
- `src/pyrogue/core/cli_engine.py` - CLI開発モード

#### CLIモード詳細
```bash
# CLIモードでの起動
python -m pyrogue.main --cli

# 利用可能なコマンド例
> move north    # 北へ移動
> get           # アイテム取得
> use potion    # ポーション使用
> attack        # 攻撃
> status        # ステータス表示
> quit          # ゲーム終了
```

**特徴**:
- **統一コマンドセット**: GUIと同じ操作がテキストで可能
- **自動化対応**: スクリプトによる自動テスト
- **開発効率**: デバッグとテストの高速化

## 今後の拡張予定

### 1. ダンジョン生成バリエーション

#### 実装予定
- **孤立部屋群**: 隠し通路でのみアクセス可能な部屋群
- **暗い部屋**: 照明なしでは視界効かない特殊部屋
- **洞窟システム**: 不規則な自然洞窟風ダンジョン

#### 技術的詳細
- **IsolatedRoomBuilder**: 孤立部屋群専用ビルダー
- **DarkRoomManager**: 暗い部屋の光源管理
- **CaveGenerator**: 洞窟風生成アルゴリズム

### 2. 将来の拡張機能

#### NPCシステム拡張（オリジナルRogue非対応）
- **商人システム完全統合**: より複雑な経済システム
- **クエストシステム**: 複数の任務・報酬システム
- **NPC行動AI**: 動的な行動パターン
- **外部会話データ**: ファイルベースの会話管理

#### 追加コンテンツ
- **新魔法**: 追加の魔法種類・効果
- **新アイテム**: 特殊効果のアイテム
- **新モンスター**: 特殊能力を持つモンスター

### 3. 技術的改善

#### 性能向上
- **描画最適化**: 差分描画の改善
- **メモリ効率**: データ構造の最適化
- **並列処理**: マルチスレッド対応

#### 機能拡張
- **サウンド**: 効果音・BGM
- **グラフィック**: タイルベース表示
- **ネットワーク**: マルチプレイヤー対応

## まとめ

PyRogueは、**オリジナルRogue（1980年代）の忠実な再現**と**現代的な拡張機能**を融合した、完全に機能する本格的なローグライクゲームです。

### 🎯 **完成度の高い機能群**
- **オリジナルRogue準拠**: 26階層、手続き生成、パーマデス、識別システム
- **現代的拡張**: NPCシステム、多様なAI、幻覚システム、スコアランキング
- **高品質アーキテクチャ**: Builder Pattern、責務分離、包括的テスト

### 🏗️ **技術的優秀さ**
- **26個のテストファイル**: 包括的なテストカバレッジ
- **Builder Pattern**: 拡張性の高いダンジョン生成システム
- **CLI/GUIデュアルモード**: 開発効率とユーザビリティを両立
- **完全な型ヒント**: 高い保守性と開発効率

### 🎮 **ゲーム体験の充実**
- **真のローグライク体験**: 完全なPermadeathシステム
- **豊富な戦略性**: 多様なモンスターAI、状態異常、魔法システム
- **探索の楽しさ**: 迷路階層、隠し扉、トラップシステム
- **成長システム**: 詳細な統計とスコアランキング

### 🔧 **開発・保守性**
- **高い拡張性**: 新しいダンジョンタイプ、AI、アイテムの追加が容易
- **包括的ドキュメント**: 開発ガイド、アーキテクチャ文書
- **一貫したコーディング規約**: 日本語コメント、PEP 8準拠

PyRogueは、単なるゲームではなく、**高品質なソフトウェア開発のベストプラクティス**を実践した、教育的価値の高いプロジェクトでもあります。各機能は独立性を保ちながら有機的に連携し、一貫性のあるゲーム体験を実現しています。
