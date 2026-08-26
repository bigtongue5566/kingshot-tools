# 玩家 ID 名冊

使用者希望玩家改名後仍能辨識同一帳號時，使用本文件。

## 身分邊界

- 以遊戲內 `Governor ID`／`Player ID` 當主鍵，欄位名為 `governor_id`。
- `tracker_uid` 是第三方資料庫內部鍵，不可取代或冒充遊戲內 ID。
- 名稱、王國、聯盟、Power、Mystic 與榜單排名都可能改變或重複；它們是比對證據，不是身分主鍵。
- 公開榜單可能沒有遊戲內 ID。沒有可辯護的比對前，讓 `governor_id` 留白；不可拿其他數字補上。
- 優先使用玩家遊戲內個人資料複製的 ID。第三方的同名／同國精確查詢可作候選，但在遊戲內或另一獨立來源確認前仍屬待確認。

## 名冊 CSV

每個 `governor_id` 只保留一筆目前列：

```text
governor_id,tracker_uid,current_kingdom,current_name,known_names,
provided_label,rank_hint,match_status,id_source,id_last_checked,notes
```

- `known_names`：已確認的舊可見名稱，以 ` | ` 分隔，保留原始 Unicode 與拼寫。
- `provided_label`：使用者最初提供的簡稱或拼寫；不等於已確認舊名。
- `rank_hint`：明確標示的歷史排名，不可重新解讀為 ID。
- `match_status`：至少區分 `in_game_confirmed`、`third_party_exact_pending`、`high_confidence_candidate`、`unresolved_candidate`。
- `id_source`：說明 ID 來源；若來自其他服務，不可假裝由 KS Atlas 提供。
- `id_last_checked`：身分查詢日期，格式 `YYYY-MM-DD`；它不是榜單快照日期。

用 `scripts/upsert_player_registry.py` 更新名冊。可見名稱改變時，腳本會先把舊目前名稱放進 `known_names` 再寫入新名稱。人工核對後才可把狀態升級為 `in_game_confirmed`。

## 報告顯示

名冊是可重建的來源資料。只有使用者要求並理解報告會暴露持久帳號識別碼時，才把 Governor ID 放進公開報告。其他情況在內部用 ID 去重，公開只顯示目前名稱，必要時加上精簡曾用名。
