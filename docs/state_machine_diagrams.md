---
cache_control: {"type": "ephemeral"}
---
# PyRogue - ステートマシン図

## 概要

このドキュメントでは、PyRogueの各システムにおける状態遷移をステートマシン図で視覚化しています。ゲーム状態の管理、プレイヤーの行動フロー、UIの状態遷移、AIの行動パターンを明確に定義し、実装時の状態管理の指針を提供します。

## 1. ゲーム全体状態遷移

### 1.1 メインゲーム状態遷移

```mermaid
stateDiagram-v2
    [*] --> MENU : ゲーム起動

    MENU --> PLAYERS_TURN : New Game
    MENU --> PLAYERS_TURN : Load Game
    MENU --> [*] : Exit

    PLAYERS_TURN --> ENEMY_TURN : ターン消費アクション
    PLAYERS_TURN --> SHOW_INVENTORY : 'i' キー
    PLAYERS_TURN --> SHOW_MAGIC : 'z' キー
    PLAYERS_TURN --> CHARACTER_SCREEN : キャラクター画面
    PLAYERS_TURN --> TARGETING : 魔法ターゲット選択
    PLAYERS_TURN --> DIALOGUE : NPC対話開始
    PLAYERS_TURN --> PLAYER_DEAD : HP=0
    PLAYERS_TURN --> VICTORY : イェンダーのアミュレット獲得

    ENEMY_TURN --> PLAYERS_TURN : 敵ターン完了
    ENEMY_TURN --> PLAYER_DEAD : プレイヤー死亡

    SHOW_INVENTORY --> PLAYERS_TURN : ESC/閉じる
    SHOW_INVENTORY --> DROP_INVENTORY : ドロップモード

    DROP_INVENTORY --> SHOW_INVENTORY : アイテムドロップ完了
    DROP_INVENTORY --> PLAYERS_TURN : ESC/キャンセル

    SHOW_MAGIC --> PLAYERS_TURN : ESC/閉じる
    SHOW_MAGIC --> TARGETING : 魔法選択

    TARGETING --> PLAYERS_TURN : ターゲット選択完了
    TARGETING --> SHOW_MAGIC : ESC/キャンセル

    CHARACTER_SCREEN --> PLAYERS_TURN : ESC/閉じる
    CHARACTER_SCREEN --> LEVEL_UP : レベルアップ

    LEVEL_UP --> PLAYERS_TURN : 能力選択完了

    DIALOGUE --> PLAYERS_TURN : 対話終了

    PLAYER_DEAD --> GAME_OVER : 死亡処理
    VICTORY --> [*] : 勝利画面終了
    GAME_OVER --> MENU : リスタート
    GAME_OVER --> [*] : ゲーム終了

    note right of PLAYERS_TURN
        プレイヤーの行動待ち状態
        - 移動、攻撃、アイテム使用
        - UI画面への遷移
        - セーブ・ロード操作
    end note

    note right of ENEMY_TURN
        敵の行動処理状態
        - モンスターAI実行
        - 環境効果適用
        - 状態異常処理
    end note
```

### 1.2 UI状態詳細遷移

```mermaid
stateDiagram-v2
    [*] --> UI_GAME : ゲーム開始

    UI_GAME --> UI_MENU : ESCキー
    UI_GAME --> UI_INVENTORY : 'i' キー
    UI_GAME --> UI_MAGIC : 'z' キー
    UI_GAME --> UI_CHARACTER : 'c' キー
    UI_GAME --> UI_HELP : '?' キー

    UI_MENU --> UI_GAME : メニュー選択
    UI_MENU --> [*] : ゲーム終了

    UI_INVENTORY --> UI_GAME : ESC/閉じる
    UI_INVENTORY --> UI_INVENTORY_DROP : 'd' ドロップモード
    UI_INVENTORY --> UI_INVENTORY_USE : 'u' 使用モード
    UI_INVENTORY --> UI_INVENTORY_EQUIP : 'e' 装備モード
    UI_INVENTORY --> UI_HELP : '?' ヘルプ

    UI_INVENTORY_DROP --> UI_INVENTORY : ドロップ完了
    UI_INVENTORY_USE --> UI_INVENTORY : 使用完了
    UI_INVENTORY_EQUIP --> UI_INVENTORY : 装備完了

    UI_MAGIC --> UI_GAME : ESC/閉じる
    UI_MAGIC --> UI_TARGETING : 魔法選択
    UI_MAGIC --> UI_HELP : '?' ヘルプ

    UI_TARGETING --> UI_GAME : ターゲット選択完了
    UI_TARGETING --> UI_MAGIC : ESC/キャンセル

    UI_CHARACTER --> UI_GAME : ESC/閉じる
    UI_CHARACTER --> UI_LEVELUP : レベルアップ処理

    UI_LEVELUP --> UI_CHARACTER : 能力選択完了

    UI_HELP --> UI_GAME : 任意キー
    UI_HELP --> UI_INVENTORY : インベントリヘルプ終了
    UI_HELP --> UI_MAGIC : 魔法ヘルプ終了

    note right of UI_INVENTORY
        インベントリ画面の状態
        - アイテム一覧表示
        - 装備状態表示
        - 使用・装備・ドロップ操作
    end note

    note right of UI_TARGETING
        ターゲット選択状態
        - カーソル移動
        - 有効ターゲットの表示
        - 射程・視界チェック
    end note
```

## 2. プレイヤー行動状態遷移

### 2.1 プレイヤーターン詳細状態

```mermaid
stateDiagram-v2
    [*] --> WAITING_INPUT : ターン開始

    WAITING_INPUT --> PROCESSING_MOVE : 移動キー入力
    WAITING_INPUT --> PROCESSING_ATTACK : 攻撃アクション
    WAITING_INPUT --> PROCESSING_ITEM : アイテム操作
    WAITING_INPUT --> PROCESSING_MAGIC : 魔法詠唱
    WAITING_INPUT --> PROCESSING_SPECIAL : 特殊アクション
    WAITING_INPUT --> UI_STATE : UI操作

    PROCESSING_MOVE --> CHECKING_MOVE : 移動妥当性チェック
    CHECKING_MOVE --> EXECUTING_MOVE : 移動可能
    CHECKING_MOVE --> WAITING_INPUT : 移動不可

    EXECUTING_MOVE --> CHECKING_ITEMS : 移動完了
    CHECKING_ITEMS --> AUTO_PICKUP : ゴールド回収
    CHECKING_ITEMS --> CHECKING_TRAPS : アイテムなし
    AUTO_PICKUP --> CHECKING_TRAPS : 回収完了

    CHECKING_TRAPS --> TRAP_TRIGGERED : トラップ発動
    CHECKING_TRAPS --> TURN_END : トラップなし
    TRAP_TRIGGERED --> APPLYING_TRAP : トラップ効果適用
    APPLYING_TRAP --> TURN_END : 効果適用完了

    PROCESSING_ATTACK --> SELECTING_TARGET : ターゲット選択
    SELECTING_TARGET --> EXECUTING_COMBAT : ターゲット確定
    SELECTING_TARGET --> WAITING_INPUT : キャンセル
    EXECUTING_COMBAT --> TURN_END : 戦闘完了

    PROCESSING_ITEM --> ITEM_SELECTION : アイテム選択
    ITEM_SELECTION --> USING_ITEM : アイテム使用
    ITEM_SELECTION --> WAITING_INPUT : キャンセル
    USING_ITEM --> APPLYING_EFFECT : 効果適用
    APPLYING_EFFECT --> TURN_END : 効果完了

    PROCESSING_MAGIC --> SPELL_SELECTION : 魔法選択
    SPELL_SELECTION --> CHECKING_MP : MP確認
    CHECKING_MP --> SPELL_TARGETING : MP充分
    CHECKING_MP --> WAITING_INPUT : MP不足
    SPELL_TARGETING --> CASTING_SPELL : ターゲット選択完了
    CASTING_SPELL --> TURN_END : 詠唱完了

    PROCESSING_SPECIAL --> SEARCHING : 探索アクション
    PROCESSING_SPECIAL --> DISARMING : 解除アクション
    PROCESSING_SPECIAL --> OPENING_DOOR : ドア開放
    PROCESSING_SPECIAL --> CLOSING_DOOR : ドア閉鎖
    PROCESSING_SPECIAL --> USING_STAIRS : 階段使用

    SEARCHING --> TURN_END : 探索完了
    DISARMING --> TURN_END : 解除完了
    OPENING_DOOR --> TURN_END : ドア開放完了
    CLOSING_DOOR --> TURN_END : ドア閉鎖完了
    USING_STAIRS --> FLOOR_CHANGE : 階層移動

    FLOOR_CHANGE --> [*] : 新フロア開始

    UI_STATE --> WAITING_INPUT : UI操作完了
    TURN_END --> [*] : ターン終了

    note right of WAITING_INPUT
        プレイヤー入力待ち
        - キー入力の受付
        - コマンド解析
        - アクション種別決定
    end note

    note right of CHECKING_MOVE
        移動妥当性チェック
        - 移動先の壁判定
        - ドアの開閉状態
        - モンスターの存在
    end note
```

### 2.2 戦闘状態遷移

```mermaid
stateDiagram-v2
    [*] --> COMBAT_INIT : 戦闘開始

    COMBAT_INIT --> CHECKING_DISTANCE : 距離チェック
    CHECKING_DISTANCE --> MELEE_COMBAT : 隣接戦闘
    CHECKING_DISTANCE --> RANGED_COMBAT : 遠距離戦闘
    CHECKING_DISTANCE --> [*] : 戦闘不可

    MELEE_COMBAT --> CALCULATING_DAMAGE : ダメージ計算
    RANGED_COMBAT --> CALCULATING_DAMAGE : ダメージ計算

    CALCULATING_DAMAGE --> CHECKING_CRITICAL : クリティカル判定
    CHECKING_CRITICAL --> APPLYING_DAMAGE : ダメージ適用

    APPLYING_DAMAGE --> CHECKING_DEATH : 死亡判定
    CHECKING_DEATH --> ENEMY_DEATH : 敵死亡
    CHECKING_DEATH --> APPLYING_STATUS : 敵生存

    ENEMY_DEATH --> GAINING_EXP : 経験値獲得
    GAINING_EXP --> CHECKING_LEVELUP : レベルアップ判定
    CHECKING_LEVELUP --> LEVEL_UP : レベルアップ
    CHECKING_LEVELUP --> COMBAT_END : レベル据え置き
    LEVEL_UP --> COMBAT_END : レベルアップ完了

    APPLYING_STATUS --> CHECKING_SPECIAL : 特殊効果判定
    CHECKING_SPECIAL --> SPECIAL_EFFECT : 特殊効果発動
    CHECKING_SPECIAL --> COMBAT_END : 特殊効果なし
    SPECIAL_EFFECT --> COMBAT_END : 効果適用完了

    COMBAT_END --> [*] : 戦闘終了

    note right of CALCULATING_DAMAGE
        ダメージ計算処理
        - 基本ダメージ = 攻撃力 - 防御力
        - 最低1ダメージ保証
        - 装備・状態異常による修正
    end note

    note right of CHECKING_CRITICAL
        クリティカルヒット判定
        - 5%の確率で発動
        - ダメージ2倍
        - 特別なメッセージ表示
    end note
```

## 3. モンスターAI状態遷移

### 3.1 基本モンスターAI

```mermaid
stateDiagram-v2
    [*] --> AI_IDLE : AI初期化

    AI_IDLE --> DETECTING_PLAYER : プレイヤー検出

    DETECTING_PLAYER --> PLAYER_DETECTED : プレイヤー発見
    DETECTING_PLAYER --> AI_IDLE : プレイヤー未発見

    PLAYER_DETECTED --> CALCULATING_DISTANCE : 距離計算

    CALCULATING_DISTANCE --> ATTACKING : 隣接距離
    CALCULATING_DISTANCE --> MOVING_TOWARD : 遠距離
    CALCULATING_DISTANCE --> SPECIAL_ACTION : 特殊距離

    ATTACKING --> COMBAT_RESOLUTION : 攻撃実行
    COMBAT_RESOLUTION --> CHECKING_SURVIVAL : 生存確認

    CHECKING_SURVIVAL --> AI_DEAD : モンスター死亡
    CHECKING_SURVIVAL --> CHECKING_PLAYER_DEAD : モンスター生存

    CHECKING_PLAYER_DEAD --> VICTORY_STATE : プレイヤー撃破
    CHECKING_PLAYER_DEAD --> DETECTING_PLAYER : プレイヤー生存

    MOVING_TOWARD --> PATHFINDING : 経路探索
    PATHFINDING --> EXECUTING_MOVE : 移動実行
    PATHFINDING --> BLOCKED_PATH : 経路遮断

    EXECUTING_MOVE --> DETECTING_PLAYER : 移動完了
    BLOCKED_PATH --> WAITING : 待機
    WAITING --> DETECTING_PLAYER : 待機完了

    SPECIAL_ACTION --> SPECIAL_ABILITY : 特殊能力実行
    SPECIAL_ABILITY --> DETECTING_PLAYER : 能力実行完了

    AI_DEAD --> [*] : AI終了
    VICTORY_STATE --> [*] : 勝利状態

    note right of DETECTING_PLAYER
        プレイヤー検出処理
        - FOV内でのプレイヤー探知
        - 最後に見た位置の記憶
        - 音による探知（未実装）
    end note

    note right of PATHFINDING
        経路探索処理
        - A*アルゴリズム（簡易版）
        - 障害物回避
        - 最短経路選択
    end note
```

### 3.2 特殊モンスターAI状態

```mermaid
stateDiagram-v2
    [*] --> SPECIAL_AI_INIT : 特殊AI初期化

    SPECIAL_AI_INIT --> EVALUATING_SITUATION : 状況評価

    EVALUATING_SITUATION --> AGGRESSIVE_MODE : 攻撃的判定
    EVALUATING_SITUATION --> DEFENSIVE_MODE : 防御的判定
    EVALUATING_SITUATION --> SPECIAL_MODE : 特殊行動判定

    AGGRESSIVE_MODE --> CHARGING_ATTACK : 突撃攻撃
    AGGRESSIVE_MODE --> RANGED_ATTACK : 遠距離攻撃
    AGGRESSIVE_MODE --> BERSERKER_MODE : 狂戦士化

    DEFENSIVE_MODE --> FLEEING : 逃走
    DEFENSIVE_MODE --> SUMMONING_HELP : 援軍召喚
    DEFENSIVE_MODE --> DEFENSIVE_SPELL : 防御魔法

    SPECIAL_MODE --> STEALING_ITEMS : アイテム窃取
    SPECIAL_MODE --> DRAINING_LEVEL : レベル吸収
    SPECIAL_MODE --> SPLITTING : 分裂
    SPECIAL_MODE --> ILLUSION_CAST : 幻覚攻撃

    CHARGING_ATTACK --> COMBAT_ENGAGED : 戦闘突入
    RANGED_ATTACK --> MAINTAINING_DISTANCE : 距離維持
    BERSERKER_MODE --> FRENZIED_ATTACKS : 乱舞攻撃

    FLEEING --> ESCAPE_ROUTE : 逃走経路探索
    SUMMONING_HELP --> WAITING_REINFORCEMENT : 援軍待機
    DEFENSIVE_SPELL --> PROTECTED_STATE : 防御状態

    STEALING_ITEMS --> ITEM_STOLEN : 窃取成功
    DRAINING_LEVEL --> LEVEL_DRAINED : 吸収成功
    SPLITTING --> NEW_MONSTERS : 新個体生成
    ILLUSION_CAST --> HALLUCINATION_ACTIVE : 幻覚発動

    COMBAT_ENGAGED --> EVALUATING_SITUATION : 戦闘評価
    MAINTAINING_DISTANCE --> EVALUATING_SITUATION : 状況再評価
    FRENZIED_ATTACKS --> EXHAUSTED : 疲労状態

    ESCAPE_ROUTE --> ESCAPED : 逃走成功
    WAITING_REINFORCEMENT --> REINFORCED : 援軍到着
    PROTECTED_STATE --> EVALUATING_SITUATION : 保護継続

    ITEM_STOLEN --> EVALUATING_SITUATION : 窃取後評価
    LEVEL_DRAINED --> EVALUATING_SITUATION : 吸収後評価
    NEW_MONSTERS --> EVALUATING_SITUATION : 分裂後評価
    HALLUCINATION_ACTIVE --> EVALUATING_SITUATION : 幻覚後評価

    EXHAUSTED --> RECOVERING : 回復中
    RECOVERING --> EVALUATING_SITUATION : 回復完了

    ESCAPED --> [*] : AI終了（逃走）
    REINFORCED --> EVALUATING_SITUATION : 援軍と合流

    note right of STEALING_ITEMS
        アイテム窃取処理
        - インベントリからランダム選択
        - 窃取成功率判定
        - 窃取したアイテムの処理
    end note

    note right of SPLITTING
        分裂処理
        - HP閾値での分裂発動
        - 新個体の生成
        - 分裂元の能力調整
    end note
```

## 4. ダンジョン生成状態遷移

### 4.1 ダンジョン生成プロセス

```mermaid
stateDiagram-v2
    [*] --> GENERATION_START : 生成開始

    GENERATION_START --> DETERMINING_TYPE : ダンジョンタイプ決定

    DETERMINING_TYPE --> BSP_GENERATION : BSPダンジョン
    DETERMINING_TYPE --> MAZE_GENERATION : 迷路ダンジョン
    DETERMINING_TYPE --> SPECIAL_GENERATION : 特殊ダンジョン

    BSP_GENERATION --> BSP_SPLITTING : BSP分割
    BSP_SPLITTING --> ROOM_CREATION : 部屋生成
    ROOM_CREATION --> CORRIDOR_CONNECTION : 通路接続
    CORRIDOR_CONNECTION --> DOOR_PLACEMENT : ドア配置

    MAZE_GENERATION --> MAZE_INITIALIZATION : 迷路初期化
    MAZE_INITIALIZATION --> MAZE_CARVING : 迷路彫刻
    MAZE_CARVING --> MAZE_COMPLETION : 迷路完成

    SPECIAL_GENERATION --> SPECIAL_LAYOUT : 特殊レイアウト
    SPECIAL_LAYOUT --> SPECIAL_FEATURES : 特殊要素配置

    DOOR_PLACEMENT --> ENTITY_PLACEMENT : エンティティ配置
    MAZE_COMPLETION --> ENTITY_PLACEMENT : エンティティ配置
    SPECIAL_FEATURES --> ENTITY_PLACEMENT : エンティティ配置

    ENTITY_PLACEMENT --> MONSTER_SPAWNING : モンスター配置
    MONSTER_SPAWNING --> ITEM_SPAWNING : アイテム配置
    ITEM_SPAWNING --> TRAP_SPAWNING : トラップ配置
    TRAP_SPAWNING --> STAIRS_PLACEMENT : 階段配置

    STAIRS_PLACEMENT --> VALIDATION : 生成検証

    VALIDATION --> GENERATION_SUCCESS : 検証成功
    VALIDATION --> REGENERATION : 検証失敗

    REGENERATION --> DETERMINING_TYPE : 再生成

    GENERATION_SUCCESS --> [*] : 生成完了

    note right of BSP_SPLITTING
        BSP分割処理
        - 再帰的空間分割
        - 最小サイズ制約
        - アスペクト比制御
    end note

    note right of DOOR_PLACEMENT
        ドア配置処理
        - 部屋境界突破判定
        - 隣接ドア重複回避
        - ランダム状態設定
    end note
```

## 5. セーブ・ロード状態遷移

### 5.1 セーブシステム状態

```mermaid
stateDiagram-v2
    [*] --> SAVE_INIT : セーブ開始

    SAVE_INIT --> COLLECTING_DATA : データ収集

    COLLECTING_DATA --> PLAYER_DATA : プレイヤーデータ
    COLLECTING_DATA --> WORLD_DATA : ワールドデータ
    COLLECTING_DATA --> INVENTORY_DATA : インベントリデータ
    COLLECTING_DATA --> STATE_DATA : 状態データ

    PLAYER_DATA --> SERIALIZING : シリアライゼーション
    WORLD_DATA --> SERIALIZING : シリアライゼーション
    INVENTORY_DATA --> SERIALIZING : シリアライゼーション
    STATE_DATA --> SERIALIZING : シリアライゼーション

    SERIALIZING --> VALIDATING_DATA : データ検証

    VALIDATING_DATA --> CREATING_BACKUP : バックアップ作成
    VALIDATING_DATA --> SAVE_ERROR : 検証失敗

    CREATING_BACKUP --> WRITING_FILE : ファイル書き込み
    WRITING_FILE --> CALCULATING_CHECKSUM : チェックサム計算
    CALCULATING_CHECKSUM --> SAVE_SUCCESS : セーブ成功
    CALCULATING_CHECKSUM --> SAVE_ERROR : 書き込み失敗

    SAVE_ERROR --> RESTORING_BACKUP : バックアップ復元
    RESTORING_BACKUP --> [*] : セーブ失敗終了

    SAVE_SUCCESS --> [*] : セーブ成功終了

    note right of VALIDATING_DATA
        データ検証処理
        - 必須フィールド確認
        - 値の範囲チェック
        - 一貫性検証
    end note
```

### 5.2 ロードシステム状態

```mermaid
stateDiagram-v2
    [*] --> LOAD_INIT : ロード開始

    LOAD_INIT --> CHECKING_FILE : ファイル存在確認

    CHECKING_FILE --> READING_FILE : ファイル読み込み
    CHECKING_FILE --> LOAD_ERROR : ファイル不存在

    READING_FILE --> VERIFYING_CHECKSUM : チェックサム検証

    VERIFYING_CHECKSUM --> DESERIALIZING : デシリアライゼーション
    VERIFYING_CHECKSUM --> RESTORING_BACKUP : チェックサム不一致

    RESTORING_BACKUP --> READING_BACKUP : バックアップ読み込み
    READING_BACKUP --> VERIFYING_BACKUP : バックアップ検証
    VERIFYING_BACKUP --> DESERIALIZING : バックアップ有効
    VERIFYING_BACKUP --> LOAD_ERROR : バックアップ無効

    DESERIALIZING --> VALIDATING_LOADED : ロードデータ検証

    VALIDATING_LOADED --> RESTORING_PLAYER : プレイヤー復元
    VALIDATING_LOADED --> LOAD_ERROR : データ無効

    RESTORING_PLAYER --> RESTORING_WORLD : ワールド復元
    RESTORING_WORLD --> RESTORING_INVENTORY : インベントリ復元
    RESTORING_INVENTORY --> RESTORING_STATE : 状態復元

    RESTORING_STATE --> LOAD_SUCCESS : ロード成功

    LOAD_ERROR --> [*] : ロード失敗終了
    LOAD_SUCCESS --> [*] : ロード成功終了

    note right of VERIFYING_CHECKSUM
        チェックサム検証
        - SHA256ハッシュ比較
        - ファイル整合性確認
        - 改竄検出
    end note
```

## 6. 状態異常システム遷移

### 6.1 状態異常管理

```mermaid
stateDiagram-v2
    [*] --> STATUS_NORMAL : 正常状態

    STATUS_NORMAL --> POISON_APPLIED : 毒付与
    STATUS_NORMAL --> PARALYSIS_APPLIED : 麻痺付与
    STATUS_NORMAL --> CONFUSION_APPLIED : 混乱付与
    STATUS_NORMAL --> HALLUCINATION_APPLIED : 幻覚付与

    POISON_APPLIED --> POISON_ACTIVE : 毒状態
    PARALYSIS_APPLIED --> PARALYSIS_ACTIVE : 麻痺状態
    CONFUSION_APPLIED --> CONFUSION_ACTIVE : 混乱状態
    HALLUCINATION_APPLIED --> HALLUCINATION_ACTIVE : 幻覚状態

    POISON_ACTIVE --> POISON_DAMAGE : 毒ダメージ
    POISON_DAMAGE --> POISON_TICK : ターン経過
    POISON_TICK --> POISON_ACTIVE : 継続
    POISON_TICK --> STATUS_RECOVERY : 自然回復

    PARALYSIS_ACTIVE --> ACTION_BLOCKED : 行動阻害
    ACTION_BLOCKED --> PARALYSIS_TICK : ターン経過
    PARALYSIS_TICK --> PARALYSIS_ACTIVE : 継続
    PARALYSIS_TICK --> STATUS_RECOVERY : 自然回復

    CONFUSION_ACTIVE --> RANDOM_MOVEMENT : ランダム移動
    RANDOM_MOVEMENT --> CONFUSION_TICK : ターン経過
    CONFUSION_TICK --> CONFUSION_ACTIVE : 継続
    CONFUSION_TICK --> STATUS_RECOVERY : 自然回復

    HALLUCINATION_ACTIVE --> VISUAL_DISTORTION : 視覚歪曲
    VISUAL_DISTORTION --> HALLUCINATION_TICK : ターン経過
    HALLUCINATION_TICK --> HALLUCINATION_ACTIVE : 継続
    HALLUCINATION_TICK --> STATUS_RECOVERY : 自然回復

    STATUS_RECOVERY --> STATUS_NORMAL : 状態異常解除

    POISON_ACTIVE --> CURE_APPLIED : 解毒
    PARALYSIS_ACTIVE --> CURE_APPLIED : 治療
    CONFUSION_ACTIVE --> CURE_APPLIED : 治療
    HALLUCINATION_ACTIVE --> CURE_APPLIED : 治療

    CURE_APPLIED --> STATUS_NORMAL : 強制回復

    note right of POISON_DAMAGE
        毒ダメージ処理
        - 固定ダメージ値
        - HP減少処理
        - 死亡判定
    end note

    note right of RANDOM_MOVEMENT
        ランダム移動処理
        - 入力方向の無効化
        - ランダム方向決定
        - 移動可能性チェック
    end note
```

## まとめ

これらのステートマシン図は、PyRogueの各システムにおける状態管理の詳細を視覚化しています。

### 🔄 **状態管理の設計原則**
- **明確な状態定義**: 各状態の責務と条件を明確化
- **予測可能な遷移**: 一貫した状態遷移ルール
- **エラー処理**: 異常状態への適切な対応
- **拡張性**: 新しい状態の追加容易性

### 🎯 **主要なシステム状態**
- **ゲーム状態**: 全体的なゲーム進行の管理
- **プレイヤー状態**: プレイヤーの行動と状態の詳細管理
- **AI状態**: モンスターの行動パターンと判断プロセス
- **UI状態**: ユーザーインターフェースの状態管理

### 🏗️ **実装への指針**
- 各ステートマシンは実装時の状態管理クラスの設計指針
- 状態遷移条件の明確な定義により、バグの少ない実装を実現
- エラー状態とリカバリ処理の体系的な設計
- テスト時の状態カバレッジの指針として活用可能

これらの図は、開発チームが一貫した状態管理を実装し、PyRogueの高い品質と安定性を維持するための重要な設計資料となります。
