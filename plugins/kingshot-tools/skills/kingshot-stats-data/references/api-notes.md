# Kingshot Stats API 與資料邊界

本文件只記錄會影響查詢判斷的端點與欄位。Kingshot Stats 是非官方第三方服務；公開網站端點可能未正式承諾相容性，使用前應確認目前回應結構。

## 公開網站端點

2026-08-27 實測：

```text
GET https://www.kingshotstats.com/api/search?q=<query>&limit=<n>&live=0|1
GET https://www.kingshotstats.com/api/kingdoms/<kid>?players=<n>&alliances=1
```

搜尋常見欄位：

```text
uid,fid,nick_name,power,kid,aid,alliance_abbr,alliance_name,
mystic_trial,power_rank,mystic_rank,last_active_at,last_login,from_live
```

- `fid` 對應遊戲內 `governor_id`。
- `uid` 是 Kingshot Stats 內部鍵。
- `live=1` 可能觸發較大的即時回應，並包含英雄、裝備、座標等非必要欄位。標準查詢器會捨棄這些欄位。
- `from_live=true` 表示該筆結果由這次即時查詢取得；仍應記錄查詢時間，不能當成永久位置。
- 短名稱或廣泛中文搜尋可能回傳 `{"ok":false,"error":"busy"}`。最多有限重試兩次；若已有明確王國範圍，改掃描各國名冊。
- 王國名冊通常以 Power 排序，列中的 `rank` 不可自動解讀成 Mystic 排名。

## 正式 API

文件入口：`https://api.kingshotstats.com/`

Base URL：

```text
https://api.kingshotstats.com/v1
```

以環境變數 `KINGSHOT_STATS_API_KEY` 提供金鑰；不要把金鑰寫入指令、報告、原始碼或 Git。送出時使用：

```text
Authorization: Bearer kss_...
```

常用端點：

```text
GET /v1/players/<governor_id>?include=base,ranks
GET /v1/players/<uid>?id_type=uid&include=base
GET /v1/alliances/<kid>/<tag>?include=info,roster
GET /v1/kingdoms/<kid>?include=boards&limit=100
GET /v1/kingdoms/<kid>/ranks?board=mystic_trial&limit=100
```

正式 API 預設把路徑中的玩家 ID 當作 `governor_id`。只有明確傳入 `id_type=uid` 才可用內部 `uid` 查詢；兩者數字區間可能重疊，不可猜測種類。

正式 API 文件列出的限制為每個 key 每分鐘 60 次、每日 5,000 次；玩家與聯盟區段可能最多快取 60 分鐘。回應的 `fresh`、`cached_at`、`age_seconds` 應一併保存。

## 標準輸出欄位

查詢器只保留：

```text
governor_id,tracker_uid,name,kingdom,alliance_abbr,alliance_name,
power,mystic,power_rank,mystic_rank,last_active_at,last_login,from_live
```

外層應包含：

```text
action,queried_at,source_url,live_requested,complete,results,errors
```

若是範圍掃描，只要任一王國失敗，`complete` 就必須為 `false`，並列出失敗王國；仍可交付部分結果，但不能宣稱完整覆蓋。

## 與 KS Atlas 交叉配對

KS Atlas 轉組榜單通常提供排名、王國、名稱、Mystic 與 Power，但不保證提供 Governor ID。配對步驟：

1. 保存 KS Atlas 的榜單快照日期與原始名稱。
2. 在 Kingshot Stats 以完整名稱搜尋，限制同一王國。
3. 比較聯盟、Power 和排名附近的數值；Power 不同快照有小幅差異是正常的。
4. 找到唯一候選後記為第三方精確比對；若名稱是簡稱、曾用名或有多個近似帳號，維持候選狀態。
5. 只有遊戲內 Player ID 或另一個獨立來源確認後，才升級為已確認身分。
