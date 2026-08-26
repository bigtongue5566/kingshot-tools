# 轉組研究與報告方法

## KS Atlas 即時入口

- `https://ks-atlas.com/`：王國目錄與個別王國資料。
- `https://ks-atlas.com/rankings`：王國 Mystic 比較。
- `https://ks-atlas.com/rankings/player-rankings`：轉組玩家排名。
- `https://ks-atlas.com/transfer-hub`：可見招募資訊。
- `https://ks-atlas.com/kingdom/<number>`：個別王國詳情。

KS Atlas 是非官方來源，公開頁面與 API 結構可能改變。每次調查都要確認目前頁面、網路回應、欄位標籤與快照日期。

## 指標邊界

| 指標 | 適合用途 | 不可宣稱 |
|---|---|---|
| Power | 帳號整體戰力與大課玩家規模 | 精確活動表現、指揮能力或出席率 |
| Mystic | Mystic Trial 進度與高端養成密度 | 總戰力或國籍 |
| Mystic 前 5／20 | 前線強度與榜單壓力 | 全王國活躍或士氣 |
| Mystic 前 100 總和 | 已養成玩家深度 | 總人口 |
| KvK 備戰／對戰紀錄 | 近期結果 | 只靠少數場次推定長期穩定 |
| Atlas Score | 網站定義的比較值 | Kingshot 官方分級 |

## 正規化玩家 CSV

必填欄位：

```text
kingdom,local_mystic_rank,player,mystic,power,
judgment_code,judgment,confidence,reason,direct_chinese_name,snapshot_date
```

選填欄位：

```text
transfer_group_rank,high_end_scope,alliance,source_url,source_snapshot_at,
governor_id,tracker_uid,known_names,id_match_status,id_source,id_last_checked
```

Power 與 Mystic 以未四捨五入數值保存，只在報告顯示時縮寫。保留玩家名稱原始拼寫與 Unicode。

`governor_id` 是遊戲內 Governor／Player ID，也是穩定身分主鍵。`tracker_uid` 是第三方資料庫鍵，不可當成 Governor ID。排名、王國、Power 或尾端舊排名提示都不是 ID。寫入 `governor_id` 時，同時保存比對狀態、來源、最後檢查日期和舊名稱；詳見 [player-id-registry.md](player-id-registry.md)。

## 建議比較角度

保持為分開的事實或表格，不要壓成一個沒有說明的分數：

1. 直接中文／台灣玩家名稱數。
2. 各國 Mystic 前 20 的直接名稱玩家。
3. 轉組前 100 的直接名稱玩家。
4. 直接名稱玩家中的最高 Power 與最高 Mystic。
5. 王國 Mystic 前線和前 100 深度。
6. 近期 KvK 備戰與對戰紀錄，附樣本數。
7. 預期榜單壓力。
8. 公開招募、UTC+8 活動時間、NAP、王城輪替與獎勵政策；這些需在名稱推定之外另行確認。

## 玩家排名

名稱判讀完成後使用 `scripts/rank_players.py`。

- `--sort-by power`：Power 由高到低；Power 相同者共用名次，再以 Mystic 排次序。
- `--sort-by mystic`：Mystic 由高到低；Mystic 相同者共用名次，再以 Power 排次序。
- 預設只納入直接名稱列。
- 除競賽名次外，保留實際列序號。

## 報告結構

只使用和需求有關的章節：

1. 先給依使用者目標區分的建議。
2. 資料範圍、轉組、查詢日期與快照限制。
3. Power 與 Mystic 差異。
4. 使用者要求的完整玩家排名。
5. 逐國玩家名稱覆蓋。
6. 使用者要求時加入 KvK／Mystic 比較。
7. 移民前核對清單。
8. 直接來源連結與本機可重建成果。

使用者要求玩家名稱分析時，不可從聯盟名稱推定中文社群。不要把本次報告偏好的章節永久化；以使用者指定的增刪為準。
