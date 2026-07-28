---
name: kingshot-event-data
description: Research and cross-check Kingshot event rules, scoring actions, point tables, milestones, rewards, cadence, duration, unlock requirements, schedules, and strategies using the live Kingshot Mastery event database and guides. Use when Codex needs to explain a Kingshot activity or event, identify what to save or spend, compare event stages, check current or upcoming event rotations, resolve English and Traditional Chinese event names, or update an event model or spending guide with information from kingshotmastery.com.
---

# Kingshot Event Data

Use Kingshot Mastery as a live third-party event and strategy reference. Treat the user's current in-game Event Center, scoring screen, and screenshots as authoritative when they differ from the website.

## Workflow

1. Browse live data for every request; do not rely on an earlier answer for current rules or schedules.
2. Start with the most relevant entry point:
   - `https://kingshotmastery.com/events` for the structured event database, including cadence, duration, scoring, milestones, and unlock requirements.
   - `https://kingshotmastery.com/guides/event-calendar` for recurring rotations, preparation, and broader cycle explanations.
   - `https://kingshotmastery.com/tools/event-calendar` for predicted UTC event windows.
3. If the event is missing from `/events`, search `site:kingshotmastery.com <English event name> Kingshot`. Seasonal and newly released activities may live under `/guides` or `/blog`.
4. Open the direct event or guide page. Capture its title, URL, visible updated date, cadence or date window, duration, unlock or kingdom-age conditions, scoring actions, milestones, and source-labeled strategy notes that answer the request.
5. Compare the page with the user's in-game screenshot or stated server age when available. State every material mismatch instead of silently choosing one version.
6. Cite direct Kingshot Mastery pages near the relevant claims. Label the site as an unofficial third-party source.

## Source Boundaries

- Treat exact in-game event dates, local start times, point values, rewards, and eligibility as version- and kingdom-dependent. The live in-game screen wins.
- Treat kingdom age, hero generation, Truegold stage, and feature unlocks as candidate-variant selectors, not proof of exact pack or reward contents. Require in-game or explicit player confirmation before an event CP report.
- Treat calendar-tool dates as predictions unless the page explicitly says they were verified in-client. Preserve UTC labels and convert time zones only when the user asks.
- Distinguish page facts from strategy recommendations and from your own inference.
- Prefer a page with a visible newer update date when multiple Kingshot Mastery pages conflict, but disclose the conflict.
- Never invent a missing scoring row, milestone, reward, cadence, unlock condition, or translated event name. Mark it unresolved and request an in-game screenshot when exactness matters.
- Do not claim the database covers all seasonal events merely because `/events` does not list one. Search the site's guides and blog before reporting no result.
- Keep exact quantities and point values. Do not write `約` or `approximately` unless the source itself is approximate or predicted.

## Cross-Skill Routing

- For event mechanics, stages, schedules, and strategy, use this skill.
- When the user requests a saveable per-event pack CP report, milestone stopping plan, or cheapest purchase combination, also use `$kingshot-event-report` to build the activity-specific model and report artifacts.
- For event pack prices and contents, also use `$kingshot-packs-data`; do not infer pack contents from an event guide.
- For reward or pack Gem-equivalent CP calculations, also use `$kingshot-value-calc`. Refresh Builder item values and list unresolved rewards instead of assigning them zero.
- When updating a local event model, separate source-backed facts, user-confirmed in-game rules, valuation assumptions, and calculated outputs so a later event revision can update them independently.

## Response Shape

For a general event question, return:

```text
活動：中文名稱 / English name
資料更新：頁面顯示日期（若有）
頻率與期間：
解鎖／伺服器條件：
核心玩法：
計分與里程碑：
準備與策略：
版本差異或待確認項目：
來源：
```

Omit sections that are irrelevant. For current schedules, include the source time zone, the lookup date, and a reminder to confirm the in-game Event Center.
