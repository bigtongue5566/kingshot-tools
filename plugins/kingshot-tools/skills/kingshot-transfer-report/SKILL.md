---
name: kingshot-transfer-report
description: Research Kingshot transfer groups and kingdom ranges with live KS Atlas data, audit visible player names for Chinese-language signals, compare Power, Mystic, and KvK, and create reproducible Traditional Chinese CSV, Markdown, or PDF migration reports. Use when a user asks where to migrate, requests a detailed K-range investigation, wants Chinese or Taiwanese player-name analysis, or needs a player list ranked by Power or Mystic. Do not use for event rules, pack contents, or CP valuation.
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

## Publication Boundary

Creating local artifacts does not authorize uploading, overwriting a public file, changing share permissions, creating a short URL, or publishing to another repository. Obtain explicit authorization for the exact current payload immediately before each external publication step. If a public report expands to include player names, Power, Mystic, or another detailed roster, describe that expansion before requesting authorization.
