---
name: kingshot-stats-data
description: 使用 Kingshot Stats 依玩家名稱或 Governor ID 查詢目前名稱、王國、聯盟、Power、Mystic 與排名，區分遊戲內 ID 和第三方 uid，並以可追溯的繁體中文結果協助確認改名、移民與玩家身分。當使用者要找玩家、確認現在在哪國、查 Governor ID、追蹤改名、查王國名冊或核對 KS Atlas 排名身分時使用；不要用於活動規則、禮包內容、CP 估值或只靠名稱推定國籍。
---

# Kingshot Stats 玩家資料

使用 [Kingshot Stats](https://www.kingshotstats.com/) 的公開網站資料或需 API key 的正式 API 查詢玩家與王國。這是非官方第三方來源；每次都要記錄查詢時間、來源 URL、快取／即時狀態，並以使用者的遊戲內畫面為最終依據。

## 適用範圍

- 依 Governor ID 或名稱找玩家。
- 確認玩家目前名稱、王國、聯盟、Power、Mystic 與本國排名。
- 找出改名或移民後的同一帳號，建立名稱歷史。
- 取得王國玩家名冊，或在指定王國區間搜尋名稱。
- 把 KS Atlas 的榜單名稱與 Kingshot Stats 的 Governor ID 交叉配對。

整體移民王國比較、中文名稱全量判讀與 PDF 報告使用 `$kingshot-transfer-report`；本技能負責玩家身分與目前狀態資料，不以聯盟、語言欄位或名稱推定國籍。

## 身分欄位不變量

- `governor_id`／`fid`：遊戲內 Governor ID／Player ID，是追蹤帳號的主鍵。
- `uid`：Kingshot Stats 的內部追蹤 ID，輸出時命名為 `tracker_uid`；不可當作 Governor ID。
- 名稱、王國、聯盟、Power、Mystic 與排名都可能改變，只能當比對證據。
- 使用者提供的暱稱或簡稱先放在 `provided_label`；未經 ID 或其他證據確認，不可直接寫成 `known_names`。
- 名稱搜尋有多筆結果時，不可把第一筆自動當成目標。至少核對王國、聯盟、Power、排名或 Governor ID。

## 查詢流程

1. 優先取得 Governor ID；使用者問「現在在哪」時，以 ID 查詢並加上 `--live`。
2. 只有名稱時先做一般搜尋，再用王國範圍、聯盟或排名縮小候選。短中文詞若回傳 `busy`，不要無限重試；改用明確的 `range-name` 掃描指定王國區間。
3. 只回報任務需要的欄位。除非使用者明確要求，不顯示座標、英雄、裝備或完整原始回應。
4. 若要核對轉組 Mystic 排名，先從 KS Atlas 取得排名、王國、名稱與快照，再用本 skill 查 ID 和目前位置；兩個來源的資料時間要分開寫。
5. 查詢結果應標示 `live_requested`、`from_live`、`queried_at` 和 `source_url`。沒有 `from_live=true` 時，不可稱為遊戲當下的即時位置。
6. 公開報告若要放 Governor ID，先確認使用者知道這是持久帳號識別碼；未授權時可在內部名冊使用，但公開表格只顯示名稱。

## 查詢指令

使用 `scripts/kingshot_stats_lookup.py`，它只輸出身分核對需要的標準化欄位。

依 Governor ID 查詢；只有需要確認目前位置時才加 `--live`：

```powershell
uv run python <skill-dir>\scripts\kingshot_stats_lookup.py player 286881088 --live
```

依名稱搜尋並限制王國範圍：

```powershell
uv run python <skill-dir>\scripts\kingshot_stats_lookup.py search "VIVl" --min-kingdom 1827 --max-kingdom 1883 --exact-name
```

短名稱搜尋遇到 `busy` 時，掃描指定王國區間的公開前 200 名名冊：

```powershell
uv run python <skill-dir>\scripts\kingshot_stats_lookup.py range-name "兔子" --min-kingdom 1827 --max-kingdom 1883
```

若已設定 `KINGSHOT_STATS_API_KEY`，可使用正式 API：

```powershell
uv run python <skill-dir>\scripts\kingshot_stats_lookup.py api-player 286881088 --include base,ranks
```

需要端點、欄位、錯誤處理或快取細節時，讀取 [references/api-notes.md](references/api-notes.md)。

## 回報規則

- 使用繁體中文；API 欄位與可執行參數保留英文。
- 開頭直接回答找到誰、目前在哪，以及信心等級。
- 同時列出 `governor_id` 與 `tracker_uid` 時，明確說明兩者不能互換。
- Power 與 Mystic 必須分開，且標明各自的資料時間或來源。
- 名稱搜尋未找到不代表帳號不存在；可能已改名、移民、超出公開名冊範圍或資料尚未更新。
- 公開網站或正式 API 失敗時，保留錯誤與部分覆蓋資訊；不可把不完整區間稱為完整搜尋。
