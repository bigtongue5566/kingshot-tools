---
name: kingshot-transfer-report
description: 使用即時 KS Atlas 資料研究 Kingshot 轉組與王國範圍，檢查可見玩家名稱的中文訊號，比較 Power、Mystic 與 KvK，並建立可重算的繁體中文 CSV、Markdown 或 PDF 移民報告。當使用者詢問移民去向、要求詳細王國區間調查、中文或台灣玩家名稱分析，或需要依 Power 或 Mystic 排名的玩家清單時使用；不要用於活動規則、禮包內容或 CP 估值。
---

# Kingshot Transfer Report

Research the user's current transfer range and create evidence-backed migration artifacts. Treat KS Atlas as a live unofficial third-party source; snapshot dates and the user's in-game screens take priority over earlier reports.

## Preflight

Confirm or discover these inputs before drawing conclusions:

- Kingdom range or transfer-group ID.
- Whether the user means visible Chinese-language names, Taiwan-specific name signals, or confirmed Chinese-speaking players.
- Preferred player ordering: `power` or `mystic`.
- Desired deliverables: chat summary, CSV, Markdown, PDF, or a combination.
- Sections the user wants included or omitted.

If the user says “中文玩家” without independent identity evidence, use **player-name language signals** and label the result as a visible lower bound, not a nationality census.

## Report Modes

Choose one or both modes from the user's requested title or goal. They share live data, but they are separate PDFs unless the user asks to merge them.

1. **Mystic Top 100 kingdom analysis** — title `Kingshot 移民王國分析（Mystic 前 100 名樣本）`; use the transfer-group Top 100 to compare visible high-end depth, Power, Mystic, player and alliance concentration, leaderboard pressure, and migration tradeoffs. Use [assets/mystic-top100-kingdom-analysis-template.md](assets/mystic-top100-kingdom-analysis-template.md).
2. **Full Chinese-player and kingdom investigation** — title pattern `Kingshot 轉組 K<min>–K<max>：中文玩家與王國完整調查`; audit every expected player in every kingdom and produce the complete direct-name ranking plus per-kingdom name coverage. Use [assets/transfer-report-template.md](assets/transfer-report-template.md).

Alliance concentration is permitted only as a kingdom power-structure metric in the first mode. Alliance names and tags must never identify an individual as Chinese or Taiwanese in either mode.

## Live Data Collection

1. Browse `https://ks-atlas.com/` and verify the current kingdom range, transfer-group ID, page labels, and data dates.
2. Inspect the relevant kingdom, ranking, player-ranking, and transfer-hub pages. Prefer the visible page and its current network schema over cached endpoint assumptions.
3. Capture, for every kingdom in scope:
   - Kingdom profile and KvK preparation/battle record.
   - Mystic Top 5, Top 20, and Top 100 metrics when available.
   - Every visible Mystic Top 100 player with username, local rank, Mystic, Power, and snapshot date.
   - Transfer-group Top 100 players when the group ID is available.
4. Record the lookup time, source URL, source snapshot date, missing kingdoms, and endpoint errors.
5. Use `scripts/fetch_ks_atlas.ps1` when the observed public API still matches its schema. If it differs, update the local extraction for the current task and disclose the mismatch; do not silently reuse stale fields.

Do not claim complete coverage unless every kingdom and every expected player row passed validation.

## Player-Name Audit

Read [references/name-audit.md](references/name-audit.md) before classifying Chinese or Taiwanese player-name signals.

The default invariant is strict: **judge from the player name only**. Alliance name, abbreviation, member concentration, or `TW` inside an alliance tag must not change an individual's language judgment or a kingdom's Chinese-player score. Alliance may remain as a location/contact field only when useful.

Give every player row an explicit classification, confidence, reason, and `direct_chinese_name` value. Manually review every included row and every Han, Bopomofo, `TW`, kana, Hangul, mixed-script, and pseudo-CJK candidate. Keep low-confidence romanization and single-Han candidates separate from the direct list.

## Analysis and Ranking

Read [references/report-method.md](references/report-method.md) for field definitions, comparison angles, and artifact schema.

- **Power** is the account's broad displayed combat strength.
- **Mystic** is KS Atlas's Mystic Trial progression score and is better used as a high-end development/competition proxy. It is not Power.
- Use the user's selected primary order. For equal primary values, use the other metric as the tie-breaker. Equal primary values share a competition rank.
- Generate the full direct-name list with `scripts/rank_players.py`; do not hand-sort a long table.
- Keep confirmed/direct name signals, low-confidence candidates, and no-visible-signal players separate.
- Compare kingdoms from multiple angles rather than one opaque score: visible Chinese-name count, Chinese-name players in the local Top 20, transfer Top 100 representation, Power/Mystic depth, KvK results, activity pressure, recruitment status, and time-zone fit.
- If the user requests player-name-only analysis, do not award alliance-based bonuses anywhere in the model or report.

## Reproducible Workflow

1. Fetch or transcribe the live KS Atlas snapshot.
2. Normalize all player rows to the schema in [references/report-method.md](references/report-method.md).
3. Complete the player-name audit and preserve its reasons.
4. Run the dataset validator:

   ```powershell
   uv run python <skill-dir>\scripts\validate_transfer_dataset.py players.csv --min-kingdom 1827 --max-kingdom 1883 --expected-per-kingdom 100
   ```

5. Build the requested player ranking:

   ```powershell
   uv run python <skill-dir>\scripts\rank_players.py players.csv chinese-players-by-power.csv --sort-by power
   ```

6. Draft the report using [assets/transfer-report-template.md](assets/transfer-report-template.md). Lead with recommendations and tradeoffs, then show the evidence.
7. Re-run the validator with `--ranking` after generating the ranking CSV.
8. If PDF is requested, render the Markdown or HTML, inspect representative pages and table boundaries, and verify searchable text before delivery.

## Report Rules

- Use Traditional Chinese unless the user requests another language.
- State the exact kingdom range, transfer group, lookup date, and per-source snapshot dates.
- Explain Power versus Mystic before using either for recommendations.
- Label name-derived counts as `玩家名稱可見下限` and never call them verified nationalities.
- State that English-named Chinese-speaking players are not detectable from names alone.
- Show the complete player ranking when requested; do not substitute a Top 10 excerpt.
- Keep the chosen primary ranking column visually first.
- Integrate corrections into the relevant table or summary unless the user asks for a separate correction section.
- Omit tables the user does not want. Do not preserve a generic kingdom-competition table merely because a template contains it.
- Cite direct KS Atlas pages near current factual claims and label the site unofficial.
- Do not present an old PDF, Dropbox file, or short URL as current after the report changes.

## Mystic Top 100 PDF Content Contract

When the user asks for `Kingshot 移民王國分析`, the PDF must use the transfer-group Mystic Top 100 as a clearly labeled censored sample, not as the complete population of every kingdom. It must contain:

1. **先講結論** — recommend a balanced default plus alternatives for high-end strength, distributed power, stable growth, strongest Mystic front line, and lower personal-ranking pressure. State that the final fit depends on the user's Power, Mystic, spending, language, and goals.
2. **樣本口徑與 Power／Mystic** — give the group, snapshot date, Top 100 row count, kingdom coverage, Power-versus-Mystic explanation, and the warning that sample totals are not whole-kingdom totals.
3. **核心王國比較** — compare only the relevant leading or shortlisted kingdoms with `王國／前百人數／樣本總戰力／Mystic 合計／轉組前 20 人數／最強單人戰力占比／最大聯盟 Mystic 占比／結構判讀`.
4. **從不同目標看** — separate recommendations for `想打王國戰、跟強車`, `想要健康的高端分布`, `想拿個人活動排名`, and `想加入權力中心、少處理多盟政治`.
5. **建議 shortlist** — a table with `優先級／王國／適合對象／移民前最大確認點`.
6. **這份榜單不能回答的關鍵問題** — list the missing live facts to request before migrating: recent KvK results, top-alliance power and activity, event times and languages, NAP and castle rotation, rally-leader quality, immigration cap/invitations, and planned departures.
7. **判讀限制** — state that the ranking is truncated, sample aggregates do not equal kingdom strength, alliance concentration does not prove cooperation or nationality, and the user's ability to enter a target alliance still matters.
8. **資料來源與快照** — link the KS Atlas player ranking and the relevant kingdom or ranking pages, and label the source unofficial.

Add `如果優先尋找中文／台灣玩家` only when requested. Classify that section from player names only; do not reuse alliance tags such as `CTW`, `TWN`, or `PIR` as identity evidence. If only the transfer Top 100 is available, label it as a very narrow visible lower bound and recommend the full Chinese-player mode for complete range coverage.

Before rendering, verify that kingdom sample counts sum to the declared ranking row count (normally 100), every aggregate is computed from the same snapshot, concentration percentages use documented denominators, shortlist claims match the comparison table, and the PDF tables are searchable and unclipped. If fewer than 100 rows are available, disclose the incomplete snapshot and do not call it a complete Top 100.

## Full Chinese-Player PDF Content Contract

When the user asks for a `中文玩家與王國完整調查`, a complete migration PDF, or the K1827–K1883 report, the PDF is a full deliverable rather than a short summary. Use this exact title pattern:

```text
Kingshot 轉組 K<min>–K<max>：中文玩家與王國完整調查
```

The PDF must contain all of these sections unless the user explicitly removes one:

1. **結論先講** — name the primary and alternative kingdoms by objective, with the supporting Chinese-name, Mystic, Power, and KvK facts plus each choice's main cost.
2. **各角度移民建議** — a compact table with `偏好／優先王國／為什麼／主要代價`; do not reduce the recommendation to one opaque overall score.
3. **全量逐名判讀口徑** — state the exact kingdom count, expected players per kingdom, total audited rows, T/Z/B/H/R/J/E/D/N category counts, direct-name lower bound, and the rule that alliance names were not evidence.
4. **Power 與 Mystic** — explain the difference and state which one controls the full player ranking; never present Mystic as combat Power.
5. **轉組前 100 的直接中文／台灣名稱** — list every matching player, not only the highest one, with transfer rank, kingdom, player, Mystic, Power, and judgment. Say explicitly when there are no matches.
6. **中文名稱玩家完整排名** — include every `direct_chinese_name=true` row, never a Top 10 excerpt. If sorted by Power, show `戰力名次／王國／玩家／戰力／Mystic／本國 Mystic 名次／名稱判讀`; if sorted by Mystic, place Mystic rank and Mystic first, then Power.
7. **每個王國的玩家名稱分析** — exactly one row for every kingdom in range, including direct Chinese-name count, direct-name players in the local Mystic Top 20, transfer Top 100 count, and visible examples. For K1827–K1883 this is the `57 國玩家名稱覆蓋表`.
8. **限制與移民前核對** — disclose snapshot dates, missing or small KvK samples, name-only undercount, English-name blind spots, and the in-game questions to verify: Chinese chat activity, UTC+8 event times, recruitment, NAP, castle rotation, and reward policy.
9. **資料來源** — link KS Atlas directory, kingdom rankings, player rankings, transfer hub or relevant kingdom pages, and label KS Atlas unofficial.
10. **可重建資料** — name the raw snapshot, audited player CSV, selected ranking CSV, and per-kingdom summary used to make the PDF.

The per-kingdom player-name coverage is required in a full report; a generic `57 國競爭力表` is not. Use kingdom Power, Mystic, and KvK facts inside recommendations, but do not add a separate all-kingdom competitiveness table unless the user asks for it.

Before rendering, verify these reconciliation rules:

- The complete ranking row count equals the direct-name total in the methodology table.
- The sum of per-kingdom direct-name counts equals that same total.
- Every kingdom in the requested inclusive range appears exactly once in the coverage table.
- The player table is actually ordered by the user's selected primary metric and retains the other metric as the tie-breaker.
- The conclusions use the same snapshot and counts as the tables; do not preserve old recommendations after the dataset changes.
- The PDF has searchable text, no clipped tables, repeated table headers where needed, and page breaks that keep headings with their first content row.

## Publication Boundary

Creating local artifacts does not authorize uploading, overwriting a public file, changing share permissions, creating a short URL, or publishing to another repository. Obtain explicit authorization for the exact current payload immediately before each external publication step. If a public report expands to include player names, Power, Mystic, or another detailed roster, describe that expansion before requesting authorization.
