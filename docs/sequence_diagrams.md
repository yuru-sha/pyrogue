---
cache_control: {"type": "ephemeral"}
---
# PyRogue - シーケンス図

## 概要

このドキュメントでは、PyRogueの主要なゲームシステムにおけるコンポーネント間のやり取りをシーケンス図で視覚化しています。各システムの詳細な処理フローを理解し、実装時の参考として活用できます。

## 1. ゲームループシーケンス

### 1.1 メインゲームループ

```mermaid
sequenceDiagram
    participant User
    participant Engine
    participant GameScreen
    participant InputHandler
    participant GameLogic
    participant TurnManager
    participant MonsterAI
    participant GameRenderer

    User->>Engine: キー入力
    Engine->>GameScreen: handle_key(event)
    GameScreen->>InputHandler: process_input(event)
    InputHandler->>GameLogic: handle_player_action(action)

    alt プレイヤーターン
        GameLogic->>GameLogic: process_player_action()
        GameLogic->>TurnManager: advance_turn()

        alt ターン消費アクション
            TurnManager->>MonsterAI: process_monsters()
            MonsterAI->>GameLogic: monster_action()
            GameLogic->>GameLogic: apply_environment_effects()
        end
    end

    GameLogic->>GameScreen: update_game_state()
    GameScreen->>GameRenderer: render(console)
    GameRenderer->>Engine: 描画完了
    Engine->>User: 画面更新
```

### 1.2 ターン管理詳細

```mermaid
sequenceDiagram
    participant GameLogic
    participant TurnManager
    participant Player
    participant MonsterAI
    participant StatusManager
    participant MessageLog

    GameLogic->>TurnManager: advance_turn()

    TurnManager->>Player: apply_turn_effects()
    Player->>StatusManager: process_status_effects()
    StatusManager->>MessageLog: add_status_messages()

    TurnManager->>MonsterAI: process_all_monsters()

    loop 各モンスター
        MonsterAI->>MonsterAI: calculate_monster_action()
        MonsterAI->>GameLogic: execute_monster_action()
        GameLogic->>MessageLog: add_action_message()
    end

    TurnManager->>GameLogic: turn_completed()
    GameLogic->>GameLogic: check_game_state()
```

## 2. 戦闘システムシーケンス

### 2.1 プレイヤー攻撃フロー

```mermaid
sequenceDiagram
    participant Player
    participant InputHandler
    participant GameLogic
    participant CombatManager
    participant Monster
    participant StatusManager
    participant MessageLog
    participant GameRenderer

    Player->>InputHandler: 攻撃キー入力
    InputHandler->>GameLogic: handle_attack_action()
    GameLogic->>CombatManager: process_combat(player, target)

    CombatManager->>CombatManager: calculate_damage()
    CombatManager->>CombatManager: check_critical_hit()
    CombatManager->>Monster: take_damage(damage)

    alt モンスター死亡
        Monster->>GameLogic: on_death()
        GameLogic->>Player: gain_experience()
        GameLogic->>MessageLog: add_death_message()
    else モンスター生存
        Monster->>StatusManager: check_status_effects()
        StatusManager->>MessageLog: add_damage_message()
    end

    CombatManager->>GameLogic: combat_result()
    GameLogic->>GameRenderer: mark_dirty_regions()
    GameRenderer->>Player: 戦闘結果表示
```

### 2.2 モンスターAI攻撃フロー

```mermaid
sequenceDiagram
    participant MonsterAI
    participant Monster
    participant CombatManager
    participant Player
    participant StatusManager
    participant MessageLog

    MonsterAI->>Monster: determine_action()

    alt 攻撃アクション
        Monster->>CombatManager: attack_player()
        CombatManager->>CombatManager: calculate_damage()
        CombatManager->>Player: take_damage()

        alt 特殊攻撃
            Monster->>Player: apply_special_effect()
            Player->>StatusManager: add_status_effect()
            StatusManager->>MessageLog: add_effect_message()
        end

    else 移動アクション
        Monster->>MonsterAI: move_towards_player()
        MonsterAI->>Monster: update_position()

    else 特殊アクション
        Monster->>Monster: execute_special_ability()
        Monster->>MessageLog: add_ability_message()
    end

    Monster->>MonsterAI: action_completed()
```

## 3. アイテムシステムシーケンス

### 3.1 アイテム使用フロー

```mermaid
sequenceDiagram
    participant Player
    participant InventoryScreen
    participant GameLogic
    participant Item
    participant EffectManager
    participant StatusManager
    participant IdentificationManager
    participant MessageLog

    Player->>InventoryScreen: アイテム選択
    InventoryScreen->>GameLogic: use_item(item)
    GameLogic->>Item: use(player, context)

    alt 未識別アイテム
        Item->>IdentificationManager: identify_on_use()
        IdentificationManager->>Item: set_identified(true)
        IdentificationManager->>MessageLog: add_identification_message()
    end

    Item->>EffectManager: apply_effects(player)

    alt 回復アイテム
        EffectManager->>Player: heal(amount)
        EffectManager->>MessageLog: add_healing_message()

    else 状態異常治療
        EffectManager->>StatusManager: remove_status_effect()
        StatusManager->>MessageLog: add_cure_message()

    else 能力向上
        EffectManager->>Player: modify_stats(enhancement)
        EffectManager->>MessageLog: add_enhancement_message()
    end

    alt スタック可能アイテム
        Item->>Item: decrease_quantity()
        alt 数量が0
            GameLogic->>Player: remove_from_inventory(item)
        end
    else 単発使用アイテム
        GameLogic->>Player: remove_from_inventory(item)
    end

    GameLogic->>InventoryScreen: refresh_display()
```

### 3.2 アイテム取得フロー

```mermaid
sequenceDiagram
    participant Player
    participant GameLogic
    participant FloorData
    participant Item
    participant Inventory
    participant MessageLog
    participant GameRenderer

    Player->>GameLogic: get_item_command()
    GameLogic->>FloorData: get_items_at_position(x, y)

    alt ゴールドアイテム
        FloorData->>Item: get_gold_amount()
        Item->>Player: add_gold(amount)
        FloorData->>FloorData: remove_item(gold)
        GameLogic->>MessageLog: add_gold_message()

    else 通常アイテム
        FloorData->>Item: get_item_at_position()

        alt インベントリ満杯
            GameLogic->>MessageLog: add_inventory_full_message()
        else インベントリ空きあり
            alt スタック可能
                Inventory->>Inventory: try_merge_with_existing()
                alt マージ成功
                    Inventory->>FloorData: remove_item(item)
                    GameLogic->>MessageLog: add_merge_message()
                else マージ失敗
                    Inventory->>Inventory: add_new_item(item)
                    FloorData->>FloorData: remove_item(item)
                end
            else 非スタック
                Inventory->>Inventory: add_item(item)
                FloorData->>FloorData: remove_item(item)
                GameLogic->>MessageLog: add_pickup_message()
            end
        end
    end

    GameLogic->>GameRenderer: mark_dirty_position(x, y)
```

## 4. ダンジョン生成シーケンス

### 4.1 BSPダンジョン生成フロー

```mermaid
sequenceDiagram
    participant DungeonManager
    participant DungeonDirector
    participant SectionBasedBuilder
    participant BSP
    participant Room
    participant DoorSystem
    participant EntitySpawner

    DungeonManager->>DungeonDirector: generate_floor(floor_number)
    DungeonDirector->>DungeonDirector: determine_dungeon_type()

    alt BSPダンジョン
        DungeonDirector->>SectionBasedBuilder: build(width, height)
        SectionBasedBuilder->>BSP: create_bsp_tree()
        BSP->>BSP: split_recursive()

        loop 各リーフノード
            SectionBasedBuilder->>Room: create_room_in_node()
            Room->>SectionBasedBuilder: room_created()
        end

        SectionBasedBuilder->>SectionBasedBuilder: connect_rooms()

        loop 各接続
            SectionBasedBuilder->>SectionBasedBuilder: create_l_corridor()
            SectionBasedBuilder->>DoorSystem: place_doors_on_path()
            DoorSystem->>DoorSystem: check_door_placement_rules()
        end

    else 迷路ダンジョン
        DungeonDirector->>MazeBuilder: build_maze()
        MazeBuilder->>MazeBuilder: recursive_backtracking()
    end

    SectionBasedBuilder->>EntitySpawner: populate_dungeon()

    loop エンティティ配置
        EntitySpawner->>EntitySpawner: spawn_monsters()
        EntitySpawner->>EntitySpawner: spawn_items()
        EntitySpawner->>EntitySpawner: spawn_traps()
    end

    EntitySpawner->>DungeonDirector: placement_completed()
    DungeonDirector->>DungeonManager: dungeon_ready()
```

### 4.2 ドア配置システム詳細

```mermaid
sequenceDiagram
    participant SectionBasedBuilder
    participant DoorSystem
    participant Room
    participant CorridorPath
    participant DoorValidator

    SectionBasedBuilder->>DoorSystem: place_doors_on_corridor(path)

    loop 通路の各位置
        DoorSystem->>DoorValidator: should_place_door(x, y)
        DoorValidator->>Room: is_room_boundary_wall(x, y)

        alt 部屋境界の壁
            DoorValidator->>DoorValidator: check_adjacent_doors(x, y)

            alt 隣接ドアなし
                DoorValidator->>DoorSystem: door_placement_approved()
                DoorSystem->>DoorSystem: determine_door_type()

                alt 60%確率
                    DoorSystem->>CorridorPath: place_closed_door()
                else 30%確率
                    DoorSystem->>CorridorPath: place_open_door()
                else 10%確率
                    DoorSystem->>CorridorPath: place_secret_door()
                end

                DoorSystem->>DoorSystem: register_door_position(x, y)
            end
        end
    end

    DoorSystem->>SectionBasedBuilder: door_placement_completed()
```

## 5. セーブ・ロードシステムシーケンス

### 5.1 ゲームセーブフロー

```mermaid
sequenceDiagram
    participant Player
    participant Engine
    participant SaveLoadManager
    participant GameLogic
    participant PermadeathManager
    participant DataValidator
    participant FileSystem

    Player->>Engine: Ctrl+S (セーブキー)
    Engine->>SaveLoadManager: save_game()
    SaveLoadManager->>GameLogic: create_save_data()

    GameLogic->>GameLogic: serialize_player_data()
    GameLogic->>GameLogic: serialize_dungeon_data()
    GameLogic->>GameLogic: serialize_inventory_data()
    GameLogic->>SaveLoadManager: save_data_ready()

    SaveLoadManager->>DataValidator: validate_save_data()
    DataValidator->>SaveLoadManager: validation_result()

    alt データ有効
        SaveLoadManager->>PermadeathManager: save_with_checksum()
        PermadeathManager->>FileSystem: create_backup()
        PermadeathManager->>FileSystem: write_save_file()
        PermadeathManager->>FileSystem: write_checksum()
        PermadeathManager->>SaveLoadManager: save_completed()
        SaveLoadManager->>Player: セーブ成功メッセージ

    else データ無効
        SaveLoadManager->>Player: セーブ失敗メッセージ
    end
```

### 5.2 ゲームロードフロー

```mermaid
sequenceDiagram
    participant Player
    participant Engine
    participant SaveLoadManager
    participant PermadeathManager
    participant DataValidator
    parameter GameLogic
    participant FileSystem

    Player->>Engine: Ctrl+L (ロードキー)
    Engine->>SaveLoadManager: load_game()
    SaveLoadManager->>PermadeathManager: load_with_verification()

    PermadeathManager->>FileSystem: read_save_file()
    PermadeathManager->>FileSystem: read_checksum()
    PermadeathManager->>PermadeathManager: verify_checksum()

    alt チェックサム一致
        PermadeathManager->>SaveLoadManager: save_data_loaded()

    else チェックサム不一致
        PermadeathManager->>FileSystem: restore_from_backup()
        PermadeathManager->>PermadeathManager: verify_backup_checksum()

        alt バックアップ有効
            PermadeathManager->>SaveLoadManager: backup_data_loaded()
        else バックアップ無効
            PermadeathManager->>SaveLoadManager: load_failed()
        end
    end

    alt ロード成功
        SaveLoadManager->>DataValidator: validate_loaded_data()
        DataValidator->>SaveLoadManager: validation_result()

        alt データ有効
            SaveLoadManager->>GameLogic: restore_game_state()
            GameLogic->>GameLogic: deserialize_player_data()
            GameLogic->>GameLogic: deserialize_dungeon_data()
            GameLogic->>GameLogic: deserialize_inventory_data()
            GameLogic->>SaveLoadManager: game_state_restored()
            SaveLoadManager->>Player: ロード成功メッセージ

        else データ無効
            SaveLoadManager->>Player: データ破損メッセージ
        end
    else ロード失敗
        SaveLoadManager->>Player: ロード失敗メッセージ
    end
```

## 6. トラップシステムシーケンス

### 6.1 トラップ探索・解除フロー

```mermaid
sequenceDiagram
    participant Player
    participant InputHandler
    participant GameLogic
    participant TrapSystem
    participant TrapSpawner
    participant MessageLog

    Player->>InputHandler: 's' (探索キー)
    InputHandler->>GameLogic: handle_search_action()
    GameLogic->>TrapSystem: search_adjacent_traps()

    loop 隣接8方向
        TrapSystem->>TrapSpawner: get_trap_at_position(x, y)

        alt 隠しトラップ発見
            TrapSpawner->>TrapSystem: hidden_trap_found()
            TrapSystem->>TrapSystem: calculate_search_success()

            alt 探索成功
                TrapSystem->>TrapSpawner: reveal_trap()
                TrapSystem->>MessageLog: add_trap_found_message()
            else 探索失敗
                TrapSystem->>MessageLog: add_search_failed_message()
            end
        end
    end

    Player->>InputHandler: 'd' (解除キー)
    InputHandler->>GameLogic: handle_disarm_action()
    GameLogic->>TrapSystem: disarm_adjacent_traps()

    loop 隣接8方向
        TrapSystem->>TrapSpawner: get_revealed_trap_at_position(x, y)

        alt 解除対象トラップ存在
            TrapSystem->>TrapSystem: calculate_disarm_success()

            alt 解除成功
                TrapSystem->>TrapSpawner: remove_trap()
                TrapSystem->>MessageLog: add_disarm_success_message()
            else 解除失敗
                TrapSystem->>TrapSystem: check_failure_trigger()

                alt 30%確率でトラップ発動
                    TrapSystem->>TrapSpawner: trigger_trap()
                    TrapSpawner->>Player: apply_trap_effect()
                    TrapSystem->>MessageLog: add_trap_triggered_message()
                end
            end
        end
    end
```

## 7. 魔法システムシーケンス

### 7.1 魔法詠唱フロー

```mermaid
sequenceDiagram
    participant Player
    participant MagicScreen
    participant GameLogic
    participant SpellManager
    participant TargetingSystem
    participant EffectManager
    participant MessageLog

    Player->>MagicScreen: 'z' (魔法書キー)
    MagicScreen->>Player: 魔法一覧表示
    Player->>MagicScreen: 魔法選択
    MagicScreen->>GameLogic: cast_spell(spell_id)

    GameLogic->>SpellManager: get_spell(spell_id)
    SpellManager->>SpellManager: check_mp_cost()

    alt MP不足
        SpellManager->>MessageLog: add_insufficient_mp_message()
    else MP充分
        SpellManager->>GameLogic: spell_castable()

        alt ターゲット必要
            GameLogic->>TargetingSystem: enter_targeting_mode()
            TargetingSystem->>Player: ターゲット選択モード
            Player->>TargetingSystem: ターゲット選択
            TargetingSystem->>GameLogic: target_selected()
        end

        GameLogic->>SpellManager: execute_spell(target)
        SpellManager->>Player: consume_mp(cost)
        SpellManager->>EffectManager: apply_spell_effects()

        alt 攻撃魔法
            EffectManager->>TargetingSystem: deal_magic_damage()
            EffectManager->>MessageLog: add_damage_message()

        else 回復魔法
            EffectManager->>Player: heal_hp(amount)
            EffectManager->>MessageLog: add_healing_message()

        else 状態異常魔法
            EffectManager->>TargetingSystem: apply_status_effect()
            EffectManager->>MessageLog: add_effect_message()
        end

        SpellManager->>GameLogic: spell_completed()
    end
```

## 8. NPCシステムシーケンス（現在無効化中）

### 8.1 NPC対話フロー

```mermaid
sequenceDiagram
    participant Player
    participant GameLogic
    participant NPCManager
    participant NPC
    participant DialogueScreen
    participant TradingManager
    participant MessageLog

    Note over NPCManager: 現在このシステムは無効化されています

    Player->>GameLogic: move_to_npc_position()
    GameLogic->>NPCManager: check_npc_interaction()
    NPCManager->>NPC: get_npc_at_position()

    alt NPC存在
        NPC->>DialogueScreen: start_dialogue()
        DialogueScreen->>Player: 対話選択肢表示
        Player->>DialogueScreen: 選択肢選択

        alt 取引選択
            DialogueScreen->>TradingManager: start_trading()
            TradingManager->>Player: 取引画面表示
            Player->>TradingManager: 取引操作
            TradingManager->>NPC: process_trade()
            NPC->>MessageLog: add_trade_message()

        else 情報交換選択
            DialogueScreen->>NPC: provide_information()
            NPC->>MessageLog: add_info_message()

        else 対話終了
            DialogueScreen->>GameLogic: end_dialogue()
        end
    end
```

## まとめ

これらのシーケンス図は、PyRogueの主要システムにおけるコンポーネント間の相互作用を詳細に示しています。

### 🔄 **主要な設計パターン**
- **責務分離**: 各コンポーネントが明確な役割を持つ
- **メッセージパッシング**: 疎結合なコンポーネント間通信
- **状態管理**: 一貫した状態遷移の管理
- **エラーハンドリング**: 適切な例外処理とフォールバック

### 🎯 **システム間の連携**
- **ゲームループ**: 全システムを統合する中央制御
- **戦闘システム**: ダメージ計算と状態管理の統合
- **アイテムシステム**: インベントリと効果システムの連携
- **ダンジョン生成**: BSPアルゴリズムと配置システムの協調

### 🏗️ **実装への指針**
- 各シーケンス図は実装時の詳細な参考資料として活用可能
- コンポーネント間のインターフェース設計の指針を提供
- エラーケースと正常ケースの両方を考慮した設計
- 拡張性を考慮した柔軟なアーキテクチャの実現

これらの図は、開発チームがシステムの動作を理解し、一貫した実装を行うための重要な資料となります。
