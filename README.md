# Kingshot Tools

`kingshot-tools` 是給 Codex 使用的 Kingshot 外掛，整合活動、禮包、CP 值、移民調查與中英名稱對照。它會優先產生可保存、可重算、附資料來源的成果，而不是只在對話中給出一次性的結論。

Marketplace 與 Plugin 的識別名稱皆為 `kingshot-tools`，但介面上會分別顯示為 `Kingshot Tools Marketplace` 與 `Kingshot Tools`。

## 功能

| 技能 | 用途 |
| --- | --- |
| `$kingshot-event-data` | 查詢活動玩法、計分、里程碑、獎勵、時程與準備策略 |
| `$kingshot-event-report` | 確認玩家現況後，建立可重算的活動禮包邊際 CP 報告 |
| `$kingshot-packs-data` | 查詢並交叉核對禮包價格、內容與伺服器階段差異 |
| `$kingshot-value-calc` | 將禮包物品換算為鑽石，計算每美元買到的 CP 價值 |
| `$kingshot-stats-data` | 依名稱或 Governor ID 查玩家目前王國、聯盟、Power、Mystic 與排名 |
| `$kingshot-transfer-report` | 調查轉組範圍、王國強度與中文玩家名稱，產生移民報告 |
| `$kingshot-translation-pairs` | 核對繁中與英文遊戲專有名稱，安全保存已確認的名稱配對 |

## 安裝

需求：已安裝支援外掛的 Codex 桌面版與 `codex` CLI。

1. 將這個 GitHub 儲存庫加入 Codex 外掛市集：

   ```powershell
   codex plugin marketplace add bigtongue5566/kingshot-tools
   ```

2. 回到 Codex 桌面版，依序開啟「Settings → Plugins」，找到 `Kingshot Tools` 並安裝。
3. 開啟新任務，讓 Codex 載入剛安裝的技能。

本機開發時，也可以直接加入儲存庫所在目錄：

```powershell
codex plugin marketplace add "C:\path\to\kingshot-tools"
```

## 使用範例

技能可由 Codex 依問題自動選用，也可以在提示詞中明確指定：

```text
使用 $kingshot-event-data 查詢這個活動的最新玩法、計分、里程碑與時程。
```

```text
使用 $kingshot-event-report，先確認我的伺服器進度、目前活動進度、已購禮包、剩餘資源與獎品內容，再建立追加購買的邊際 CP 報告。
```

```text
使用 $kingshot-value-calc，依我支付的美元與取得物品計算這個禮包的 CP 值。
```

```text
使用 $kingshot-stats-data 依 Governor ID 查詢這位玩家目前的名稱、王國、聯盟、Power、Mystic 與資料時間。
```

```text
使用 $kingshot-transfer-report 調查我的移民區間，並產生繁體中文移民報告。
```

```text
使用 $kingshot-translation-pairs 核對這個繁中物品名稱的正確英文名稱。
```

## 資料與判讀原則

- 活動資料來自 [Kingshot Mastery](https://kingshotmastery.com/events)，禮包與估值資料來自 [KingshotPacks](https://kingshotpacks.com/)，移民資料來自 [KS Atlas](https://ks-atlas.com/)，玩家身分與目前狀態可由 [Kingshot Stats](https://www.kingshotstats.com/) 交叉核對。這些都是非官方第三方來源。
- 活動規則、禮包內容與獎勵可能因伺服器進度或版本而異；玩家當下的遊戲畫面與可辨識截圖具有較高優先度。
- 活動報告會把目前不加購的成果與追加購買帶來的邊際收益分開，避免把既有資源誤算成禮包價值。
- 未確認的中英文專有名稱不會自行猜譯；新配對寫入前會檢查衝突。
- 移民報告只根據畫面上可見的玩家名稱判斷語言訊號，不會用聯盟標籤推測玩家語言或地區。

## 專案結構

```text
.
├─ .agents/plugins/marketplace.json
└─ plugins/kingshot-tools/
   ├─ .codex-plugin/plugin.json
   └─ skills/
      ├─ kingshot-event-data/
      ├─ kingshot-event-report/
      ├─ kingshot-packs-data/
      ├─ kingshot-stats-data/
      ├─ kingshot-transfer-report/
      ├─ kingshot-translation-pairs/
      └─ kingshot-value-calc/
```

## 更新

若已從這個市集安裝，可以在 PowerShell 更新市集內容：

```powershell
codex plugin marketplace upgrade kingshot-tools
```

更新後請在 Codex 的「Settings → Plugins」重新安裝或更新 `Kingshot Tools`，再開啟新任務測試。

## 作者

[bigtongue5566](https://github.com/bigtongue5566)
