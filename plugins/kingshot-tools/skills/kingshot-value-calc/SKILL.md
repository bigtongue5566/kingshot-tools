---
name: kingshot-value-calc
description: Calculate Kingshot pack CP value from the USD price paid and the received item quantities by refreshing item gem costs and the USD-per-Gem baseline from the KingshotPacks Custom Pack Builder, converting all items to Gems, and reporting how many USD-equivalent dollars of value each US dollar bought. Use when a user asks whether a Kingshot bundle is worth it, provides a price plus pack contents, requests a CP or value ratio, or needs an itemized Gem-value breakdown.
---

# Kingshot Value Calculator

Evaluate a user-provided Kingshot purchase with the KingshotPacks website's USD Gem baseline. Its current Builder logic uses the website's `500 Gems = US$0.99` top-up tier, which is equivalent to `1000 Gems = US$1.98`. Treat KingshotPacks as a third-party valuation source, not official in-game pricing.

## Workflow

1. Extract the exact USD price and every visible item name and quantity. If the input is a screenshot, transcribe only readable values and call out anything uncertain.
2. Refresh the Builder catalog before calculating. Search uncertain names first:

   ```powershell
   uv run python <skill-dir>\scripts\kingshot_value_calc.py --query "VIP" --refresh
   ```

3. Map each user item to one exact Builder catalog entry. Interpret quantity in the named item's unit; for example, `3 Hour Speedup x5` means five copies of that Builder item.
4. Calculate with the script:

   ```powershell
   uv run python <skill-dir>\scripts\kingshot_value_calc.py --price-usd 4.99 --item "Gems=2500" --item "3 Hour Speedup=2" --refresh
   ```

5. Report the itemized Gem value, total Gem value, website-derived USD baseline, USD-equivalent value, CP multiplier, and the sentence `每花 US$1，可獲得約 US$X 的等值物品`.
6. Link to `https://kingshotpacks.com/builder`, label it as third-party data, and state whether the item catalog and USD baseline came from live data, cached data, or the website-compatible fallback.

## Guardrails

- Keep the user's paid price in USD. Do not substitute EUR or silently apply an exchange rate.
- Derive the default USD baseline from KingshotPacks' `500 Gems` USD top-up tier. The current website value is `US$0.99 / 500 Gems`, equivalent to `US$1.98 / 1000 Gems`.
- Use `--usd-per-1000-gems` only when the user explicitly requests an alternative valuation model. Label the result as an override and never describe the website baseline as user-defined.
- Refresh once per calculation session. If live fetching fails and the script falls back to cache, disclose the cache timestamp.
- Never invent an item value. If an item is absent or ambiguous, list it as unresolved and do not present a complete CP multiplier. Offer a confirmed subtotal or lower bound only when clearly labeled.
- Do not silently treat unrecognized items as zero.
- When a reward lets the player choose one of several items, value only the option actually selected. If the selection is not fixed, show each option's Gem value or a sensitivity range instead of treating every choice as equal.
- When comparing with a named reference pack, identify it by exact `priceUSD` plus any content variant or server-age tag. Never reuse one tier's CP score for another price tier that has the same or similar pack name.
- Use exact Builder item units. Do not multiply again by an item's internal `amount` field.
- Preserve precise quantities and prices during calculation; round only the displayed USD value and CP multiplier.
- Do not equate this ratio with the user's personal progression priority. Mention bottleneck usefulness separately if the user asks for a purchase recommendation.

## Commands

List or search the live catalog:

```powershell
uv run python <skill-dir>\scripts\kingshot_value_calc.py --list --refresh
uv run python <skill-dir>\scripts\kingshot_value_calc.py --query "speedup" --refresh
```

Read many items from JSON:

```json
[
  {"name": "Gems", "quantity": 2500},
  {"name": "100 VIP XP", "quantity": 25}
]
```

```powershell
uv run python <skill-dir>\scripts\kingshot_value_calc.py --price-usd 4.99 --items-file items.json --refresh
```

Add `--json` when structured output is useful. Use `python` directly only if `uv` is unavailable.

Read [references/calculation-method.md](references/calculation-method.md) when resolving quantity semantics, reviewing formulas, or checking the expected response format.
