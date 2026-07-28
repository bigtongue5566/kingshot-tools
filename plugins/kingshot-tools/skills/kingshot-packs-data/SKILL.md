---
name: kingshot-packs-data
description: Query and cross-check Kingshot pack prices, contents, server-age variants, and CP/value assumptions using KingshotPacks pages and their live front-end pack database. Use when Codex needs to verify Kingshot recurring packs, event packs, Daily Deals, Hope Market, Hero Rally/Path of Honor, Mystery Badge, Gear Imbuement, Masters Collection, Sign-in & Earn It, Intel/Ultra monthly cards, or update a Kingshot spending guide with pack contents from kingshotpacks.com.
---

# KingshotPacks Data

Use this skill to turn KingshotPacks into a repeatable data source for Kingshot spending analysis. Treat it as a third-party pack/value reference, not as official in-game pricing.

## Workflow

1. Open the public pages first:
   - `https://kingshotpacks.com/packs` for pack browsing, item lists, gem value, and ratings.
   - `https://kingshotpacks.com/builder` for custom pack value checks when the user provides an in-game screenshot or item list.
2. If the rendered page only exposes metadata, extract the live front-end data with `scripts/kingshotpacks_fetch.py`.
3. Compare the extracted `priceUSD`, `priceEUR`, pack contents, `ages`, and item categories with the user's list.
4. For an event CP report, treat `ages` as candidate routing only. Confirm every pack tier and reward against the player's in-game screens or explicit transcription before handing data to `$kingshot-event-report`.
5. Keep prices exact when the source has exact values. Do not write "about", "approx", or "約" unless the source itself is uncertain.
6. Rank CP by the user's bottleneck, not only by the site's value score. A high-value pack is lower priority if it gives non-bottleneck resources.
7. Cite KingshotPacks pages in the final answer or guide sources, and clearly label them as third-party data.

## Extraction Script

Run from any working directory:

```powershell
uv run python <skill-dir>\scripts\kingshotpacks_fetch.py --query "Daily Deals" --query "Hope Market"
```

Useful options:

```powershell
uv run python <skill-dir>\scripts\kingshotpacks_fetch.py --query "Masters Collection" --full-items
uv run python <skill-dir>\scripts\kingshotpacks_fetch.py --query "Intel Monthly Card" --json
uv run python <skill-dir>\scripts\kingshotpacks_fetch.py --query "Hero Rally" --query "Mystery Badge" --query "Gear Imbuement" --full-items
uv run python <skill-dir>\scripts\kingshotpacks_fetch.py --all --limit 120
```

If network access fails in the sandbox, rerun the same command with the required network approval. Cache output under `C:\tmp` unless the user asks to store an artifact in the repo.

## Interpretation Rules

- Keep activity mechanics separate from pack data. When the user needs event rules, stages, scoring, milestones, schedules, or strategy, also use `$kingshot-event-data`; use KingshotPacks only to verify the attached pack's price and contents.
- When the user requests a complete event pack CP report or milestone purchase plan, also use `$kingshot-event-report`; preserve exact pack variants and purchase caps as report inputs.
- Use `priceUSD` for the user's USD budgets; do not convert from EUR when USD is present.
- Use `ages` to separate server-age variants. Example: Hope Market TG3 packs may emphasize speedups, while TG5/TG5_270 packs may emphasize Truegold.
- Never infer that an `ages` match proves the player's live pack or reward contents. For event reports, stop and request in-game confirmation when any tier, item, quantity, purchase cap, or reward differs or remains unseen.
- Do not over-read `oneTimeOnly`; the game can use it for one purchase per period/event, not necessarily permanent one-time bundles. Use the pack name and the user's observed reset cadence to decide monthly/weekly treatment.
- Treat Hero Rally / Path of Honor as an event paid track when the user is budgeting recurring activity buys. KingshotPacks may mark it `oneTimeOnly`, but public event references describe Hero Rally as a two-week activity; for a 4-week budget use `$9.99 x2 = $19.98/月` unless the user gives a different cadence.
- For `variants`, mention the variant only when it changes the item type materially, such as Hope Market `Speed` versus `Truegold`.
- Keep pack names separate from item/resource names. `Mystery Badge` is the regular pack `神秘徽章禮包`; `Gear Imbuement` is the regular pack that gives `Mithril / 秘銀`.
- When a pack is not present in KingshotPacks, say public KingshotPacks data did not confirm it and fall back to in-game contents or other sources.

## Known Pack Notes

- `Daily Deals / 每日優惠`: KingshotPacks lists Gems, Mythic General Hero Shard, Hero XP, 3 Hour Speedup, and Lv2 Resource Chest; do not infer it gives widgets, Mithril, Forgehammers, or Gold unless the current in-game pack shows that.
- `Mystery Badge / 神秘徽章禮包`: regular pack, `$4.99`, gives Mystery Badge x2500, 100 VIP XP x25, and resources.
- `Gear Imbuement`: regular pack, `$4.99`, gives Gems x2500, Mithril x1, 100 VIP XP x25, and resources.
- `Hero Rally / Path of Honor / 英雄集結：輝煌歷程`: `$9.99` paid track; recommend it only when the player can complete enough daily tasks to claim the mid/late rewards. Buying after progress is unlocked is safer than buying levels with Gems.

## Guide Update Conventions

- Preserve the user's exact USD assumptions when they provide them.
- Put price in its own column when updating pack recommendation tables.
- Use exact monthly formulas such as `$4.99 x4 = $19.96/月`.
- Use the user's explicit monthly quantity when provided, such as Daily Deals `4 包` versus `8 包`; update totals immediately after quantity changes.
- For 4-week monthly estimates: weekly packs use `x4`, Sign-in & Earn It uses `x4`, two-week activity tracks like Hero Rally use `x2`, and two-day monthly events like Mystic Divination use the user's chosen daily-buy count.
- Separate fixed recurring buys, event-flex buys, conditional buys, and high-budget buys in one sorted CP table when the user asks for a complete recommendation.
- For Kingshot guide files, include these sources when used:
  - [KingshotPacks Browse All Packs](https://kingshotpacks.com/packs)
  - [KingshotPacks Custom Pack Builder](https://kingshotpacks.com/builder)
