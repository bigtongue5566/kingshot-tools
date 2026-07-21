# Calculation Method

## Formula

For each Builder item `i`:

```text
item_gem_value_i = Builder gemCost_i * user_quantity_i
total_gem_value = sum(item_gem_value_i)
website_usd_per_1000_gems = website_500_gem_tier_price_usd / 500 * 1000
usd_equivalent = total_gem_value / 1000 * website_usd_per_1000_gems
cp_multiplier = usd_equivalent / paid_usd
gems_per_paid_usd = total_gem_value / paid_usd
```

Interpret `cp_multiplier` as the USD-equivalent value bought by each US dollar. A result of `2.90x` means every `US$1` bought `US$2.90` of value under this model.

KingshotPacks derives its USD Gem baseline from the website's `500 Gems` top-up tier. In the current website data, that tier is `US$0.99`, so:

```text
website_usd_per_1000_gems = 0.99 / 500 * 1000 = US$1.98
```

The script reads that tier from the refreshed website bundle. If the tier cannot be parsed, it uses the same `US$1.98 per 1000 Gems` fallback embedded in the website's Builder helper and discloses the fallback in the source metadata. Use `--usd-per-1000-gems` only when the user explicitly requests an alternative valuation model, and label it as an override rather than a website value.

## Quantity Semantics

Use the catalog entry as the unit:

- `Gems=2500` means 2500 individual Gems.
- `100 Gems=25` also represents 2500 Gems of value.
- `3 Hour Speedup=2` means two 3-hour items, not two minutes and not six copies.
- `100 VIP XP=25` means 25 bundles of 100 VIP XP.
- Resource entries such as `10k Food=500` mean 500 copies of that exact resource bundle.

Do not use the Builder's internal `amount` field as another multiplier. Its `gemCost` already values one named catalog entry.

## Choice Rewards

If completing a stage or milestone presents mutually exclusive rewards, calculate the chosen option only:

```text
option_gem_value = Builder gemCost of the option * displayed quantity
```

Do not add all options together, and do not assume they have equal value. When the user has not committed to one option, show an option comparison or CP sensitivity table. Separate Builder Gem value from personal progression usefulness: the highest raw Gem value may not be the player's most-needed material.

## Name Resolution

The script accepts exact Builder names and a small set of Traditional Chinese aliases. For anything else, search before calculating:

```powershell
uv run python <skill-dir>\scripts\kingshot_value_calc.py --query "英雄經驗" --refresh
```

If multiple entries could match, show the candidates and request the exact unit. Do not guess between, for example, `1 Hour Speedup` and `1 Hour Research Speedup`.

## Example

Input:

```text
Paid: US$4.99
Gems x2500
3 Hour Speedup x2
```

Builder values used:

```text
Gems: 1 Gem each
3 Hour Speedup: 2400 Gems each
```

Calculation:

```text
total_gem_value = 2500 + (2400 * 2) = 7300 Gems
website baseline = US$1.98 per 1000 Gems
usd_equivalent = 7300 / 1000 * 1.98 = US$14.454
cp_multiplier = 14.454 / 4.99 = 2.896593...
```

Present it as `7300 鑽石價值`, `US$14.45 等值`, and `CP 2.90x`.

## Response Shape

Return a compact table with these columns:

```text
物品 | 數量 | 單件鑽石價值 | 小計鑽石價值 | 小計美金價值
```

Then state:

```text
支付：US$P
總鑽石價值：G
網站換算基準：US$B / 1000 鑽石
等值美金：US$V
CP 值：V / P = Cx
結論：每花 US$1，可獲得約 US$C 的等值物品。
```

If any item remains unresolved, replace the final CP conclusion with a clear incomplete-data notice and separate confirmed versus unresolved items.
