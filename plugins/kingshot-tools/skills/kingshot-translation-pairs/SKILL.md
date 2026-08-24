---
name: kingshot-translation-pairs
description: 使用已確認的分層詞彙庫，將 Kingshot 繁中物品名稱精確對應至英文目錄名稱，亦可反向查詢，並在衝突檢查後把新確認的配對記錄於使用者擁有的 JSON 儲存區。當需要翻譯 Kingshot 專有名稱、核對遊戲截圖與英文攻略或 KingshotPacks，或避免報告誤合併相似物品時使用；英文名稱未知時先詢問使用者，不用於一般文章翻譯。
---

# Kingshot Translation Pairs

Resolve Kingshot names as identifiers, not as free-form translations. Preserve the exact item, pack, event, hero, mechanic, quantity, and variant shown by the source.

## Storage Model

- Treat [references/terms.base.json](references/terms.base.json) as the read-only glossary shipped by the skill. GitHub or plugin updates may replace it.
- Store autonomous additions only in `~/.kingshot/glossary/terms.user.json`. Never copy or merge user additions back into the installed skill automatically.
- Resolve the user data root from `KINGSHOT_DATA_DIR` when set; otherwise use `~/.kingshot`. This override is intended for tests or explicitly selected alternate storage.
- Query the effective glossary by merging base and user JSON in memory. A matching source or term may be enriched by the user layer, but conflicting metadata or mappings must stop the operation.
- If the runtime cannot write `~/.kingshot`, request narrowly scoped permission for that directory. Do not redirect persistent data into the skill directory merely to avoid permission handling.

## Workflow

1. Separate the name from its quantity. Keep `x3`, `*3`, `×3`, chest counts, and duration units unchanged while resolving only the proper noun.
2. Search the merged glossary:

   ```powershell
   uv run python <skill-dir>\scripts\lookup_kingshot_terms.py "領主寶石材料隨機寶箱" --exact
   uv run python <skill-dir>\scripts\lookup_kingshot_terms.py "Charm Guide" --exact
   ```

3. Use a single exact confirmed match as the canonical pair. Write bilingual names as `中文（English）` unless the requested output uses another format.
4. If there is no exact match, run a partial lookup without `--exact`. Treat multiple results as candidates; never choose one only because the wording is similar.
5. When the English name is unknown or unresolved, ask the user first for the exact English name, an English keyword, or a screenshot after switching the game language to English. Keep the question concise and continue collecting other inputs while waiting when possible.
6. Only use public lookup as a fallback when the user says they cannot provide the English name or explicitly asks Codex to search. In that case, query the live Builder catalog through `$kingshot-value-calc` or pack data through `$kingshot-packs-data`. Use `$kingshot-event-data` only for event, mechanic, schedule, or milestone names.
7. A user-provided keyword such as `charm` narrows candidates but does not by itself confirm the full canonical English name. Present the narrowed candidate and ask for confirmation unless a confirmed glossary entry already matches.
8. A live English catalog entry confirms the English identifier, not its Traditional Chinese localization. Confirm the Chinese-English pair with an in-game screenshot, exact player transcription, or another source that displays both names.
9. If the evidence uses a new source, add its metadata to the user JSON first:

   ```powershell
   uv run python <skill-dir>\scripts\upsert_kingshot_source.py --source-id "player-2026-08-24" --type "player-confirmed-in-game-transcription" --date "2026-08-24" --context "English-language screenshot"
   ```

10. When a pair is confirmed, autonomously update the user JSON in the same task; do not wait for a separate request to teach the skill. Use the deterministic writer rather than manually rewriting JSON:

   ```powershell
   uv run python <skill-dir>\scripts\upsert_kingshot_term.py --zh-tw "寶石手冊" --en "Charm Guide" --category "Governor Charm" --source-id "tidal-voyage-player-2026-08-18" --source-id "builder-live-2026-08-18"
   ```

11. Test both lookup directions after every glossary change. Briefly tell the user which pair was learned and that it was saved to the user glossary.

## Autonomous Evolution

- Learn automatically only after the user explicitly confirms the pair, an in-game bilingual screen shows both names, or another source directly displays both names.
- A one-language catalog result, literal translation, fuzzy search, or inferred category is not enough to learn a pair.
- Add new pairs, aliases, source IDs, verification dates, and non-conflicting notes. Do not autonomously delete a pair or reassign an existing Chinese or English identifier.
- If either side already maps to a different term, stop without modifying either JSON file and ask the user to resolve the conflict.
- Source IDs passed to the term writer must already exist in the merged `sources` object. Use the source writer first when new evidence is introduced.
- Autonomous persistence authorizes only `~/.kingshot/glossary/terms.user.json` or the explicit `KINGSHOT_DATA_DIR` equivalent. It does not authorize publication, deployment, or edits to unrelated files.
- Run either writer with `--dry-run` when evidence or collision behavior is uncertain.

## Matching Rules

- Prefer exact names and exact item categories over literal word-by-word translation.
- Keep `Charm`, `Gear`, `Design`, `Guide`, `Material Chest`, `Variety Chest`, and `Random ... Chest` distinct.
- Never silently equate `Governor Charm Material Chest` with `Random Governor Charm Material Chest`; they are separate Builder items with different values.
- Do not call a candidate `confirmed` when only one language is sourced.
- Do not translate an unknown English name from the Chinese wording before asking the user.
- Do not invent an English event or chest name that is absent from the glossary and current evidence. Leave it in Chinese and label the English name unresolved.
- Preserve the source date because live catalog names and values can change.

## Output

For a direct lookup, return the canonical Chinese name, canonical English name, confirmation status, category, and source. For an unknown English name, ask `這個名稱的遊戲內英文是什麼？如果不確定，可以提供英文關鍵字或切換英文後的截圖。` For an event or pack report, use the canonical pair consistently in data files, calculations, and Markdown; unresolved names must remain visibly unresolved rather than being valued as zero.
