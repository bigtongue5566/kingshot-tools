# Activity-Specific Modeling Guide

## Contents

1. Source ledger
2. Server-variant preflight gate
3. Select a model type
4. Establish the state and free baseline
5. Value event outcomes
6. Attribute paid value
7. Optimize purchase combinations
8. Test and report

## 1. Source Ledger

Classify every input before calculating:

| Class | Examples | Treatment |
| --- | --- | --- |
| In-game confirmed | pack contents, purchase cap, current progress | authoritative for the player's event |
| Source-backed | Kingshot Mastery duration, stages, general mechanics | cite the direct page and its visible date |
| Valuation | Builder `gemCost`, USD-per-1000-Gems baseline | refresh live and disclose cache or fallback |
| Assumption | uninterrupted play, selected reward, token carryover | expose in the report and sensitivity analysis |
| Unresolved | unreadable screenshot, unknown probability, missing reward | do not invent or silently value as zero |

Keep facts and assumptions in different JSON fields so later event revisions can update one without rewriting the other.

## 2. Server-Variant Preflight Gate

Complete this matrix before creating a calculation model:

| Group | Required evidence | Pass condition |
| --- | --- | --- |
| Server context | kingdom or server number, event date, and a relevant age or progression marker | applicable variant is identified |
| Packs | in-game screenshots or exact user transcription for every tier in scope | prices, all items, quantities, caps, resets, and prerequisites are confirmed |
| Rewards | in-game reward screens or exact user transcription | repeatable, chest, choice, milestone, and valued ranking rewards are confirmed |
| Mechanics | in-game rules plus source cross-check | free inputs, action costs, duration, resets, probabilities, conversions, and guarantees are confirmed |

KingshotPacks `ages` and a guide's kingdom-age notes narrow the candidate set but do not prove that the player's current event uses that content. Do not infer a pack or reward matrix from server age alone.

Represent the result in the model:

```json
{
  "verification": {
    "status": "confirmed",
    "serverProgressConfirmed": true,
    "packContentsConfirmed": true,
    "rewardContentsConfirmed": true,
    "mechanicsConfirmed": true,
    "confirmedBy": "player screenshots and transcription",
    "confirmedAt": "YYYY-MM-DD",
    "serverContext": {},
    "evidence": []
  }
}
```

If a required value is missing or conflicting, keep `status` as `unverified`, record it under `unresolved`, and stop before CP calculation.

## 3. Select a Model Type

Use the smallest model that matches the event. Combine types for hybrid activities.

### Deterministic accumulation

Use when time, energy, or event currency produces a fixed number of actions:

```text
actions = floor((free_capacity + purchased_capacity) / cost_per_action)
```

Model queue count, uptime, event duration, daily resets, carryover, and incomplete final actions explicitly.

### Conversion or crafting

Use when lower-tier rewards combine into higher tiers:

```text
expected_converted_value = sum(probability_i * outcome_value_i)
conversion_gain = expected_converted_value - input_value
```

Calculate the break-even value of uncertain rewards and show whether the recommendation changes across that threshold.

### Random progression

Use when actions draw rewards, clear floors, or trigger escalating odds and guarantees. Preserve the entire state needed for the next action. Calculate:

```text
P(final_state | starting_state, actions)
expected_reward = sum(P(state) * reward_value(state))
```

Use exact enumeration, convolution, or dynamic programming when the state space is manageable. Averages alone are not valid for milestone crossing or hard guarantees.

### Ranking

Separate fixed milestone rewards from leaderboard rewards. Do not assign a guaranteed value to rank-dependent rewards without a defensible rank distribution. Report leaderboard outcomes as scenarios or leave them unresolved.

### Hybrid

Compose state transitions in the real order: free collection, queue production, purchases, actions, conversion, milestone claims, and ranking. Do not collapse steps if doing so changes floors, caps, probabilities, or guarantees.

## 4. Establish the State and Free Baseline

Define a state object containing every variable that changes future value, for example:

```json
{
  "elapsedDays": 0,
  "queues": 3,
  "currency": 0,
  "actionsCompleted": 0,
  "partialProgress": 0,
  "milestonesClaimed": [],
  "inventoryByTier": {}
}
```

Calculate these states separately:

1. No-purchase free baseline.
2. Player's current confirmed state, when progress already exists.
3. State after each single pack from the same baseline.
4. State after legal purchase combinations.

Do not reset known partial progress or replace it with average progress.

## 5. Value Event Outcomes

Build one reward ledger keyed by exact Builder item names and units. For each action, floor, chest, conversion outcome, and milestone:

```text
reward_gems = sum(exact_item_quantity * Builder_gemCost)
```

If an outcome contains a choice, calculate each option separately. If an item is unresolved, return a confirmed subtotal or lower bound and prevent a complete CP claim.

For a currency that is consumed to produce rewards, set no independent currency value in the same model. The resulting action, chest, floor, conversion, and milestone rewards carry the value.

## 6. Attribute Paid Value

For a pack `p` applied to state `s`:

```text
marginal_event_value = reward_value(transition(s, p)) - reward_value(s)
pack_value = direct_pack_value(p) + marginal_event_value
usd_equivalent = pack_value / 1000 * usd_per_1000_gems
cp = usd_equivalent / paid_usd
```

This difference automatically credits a purchase for a newly crossed milestone without charging it for rewards already reachable for free.

When comparing a bundle of purchases, calculate the bundle from the same starting state. The sum of isolated single-pack CP values is not valid when packs interact through milestones, caps, conversions, or guarantees.

## 7. Optimize Purchase Combinations

Represent each purchasable option with:

```text
id, priceUSD, directItems, eventCurrency, stateEffects,
purchaseCap, resetCadence, prerequisites, independentlyPurchasable
```

Enumerate legal integer quantities. For every target:

1. Reject combinations that violate caps or prerequisites.
2. Simulate the full event state.
3. Keep combinations that reach the target at the required confidence or guarantee level.
4. Minimize cash cost.
5. Break ties by higher CP, then larger safety buffer.

Report both the mathematical minimum and a buffered plan when uptime or luck can cause failure.

## 8. Test and Report

Test at least:

- zero purchases;
- exact milestone boundaries and one action below;
- each single pack from the same baseline;
- one sequence where a prior purchase changes the next pack's marginal CP;
- maximum legal quantities;
- skipped independent tiers;
- best and worst supported uncertain values;
- probability mass sums to 1 for exact random models;
- hard guarantees at their boundary.

Generate report tables from calculation output. Keep calculations out of hand-edited prose. Record the command used and validate all local links before delivery.
