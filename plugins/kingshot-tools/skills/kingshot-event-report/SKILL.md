---
name: kingshot-event-report
description: Create, calculate, validate, and update reproducible Markdown CP reports for Kingshot event packs after confirming the player's server progression, current progress, already-purchased packs, remaining resources, pack contents, and event rewards. Default recommendations to marginal CP from the current no-additional-purchase baseline, with cumulative CP kept separate. Use when a user asks for a per-event pack report, event pack CP table, milestone stopping plan, cheapest additional pack combination, a report such as Kingshot-逐風之旅-CP值報告.md, or a recalculation after server progression, event rules, rewards, progress, purchases, or pack contents change.
---

# Kingshot Event CP Report

Create a saveable report artifact rather than returning only a chat calculation. Build one explicit model per event because activity currencies, resets, crafting, random rewards, guarantees, rankings, and milestones can behave differently.

## Mandatory Preflight Gate

Do not scaffold the report, calculate CP, or optimize purchases until all four groups below are confirmed for the player's current server variant:

1. **Server context**: kingdom or server number, event date or edition, and at least one progression marker such as kingdom open date or age, current hero generation, Truegold stage, or another feature unlock relevant to the event.
2. **Pack matrix**: every tier in scope with exact displayed price, every item and quantity, event currency, purchase cap, reset cadence, prerequisites, and whether tiers are independently purchasable.
3. **Reward matrix**: repeatable action, floor, chest, crafting, choice, milestone, and valued ranking rewards with exact quantities; include probabilities, conversion ratios, and guarantees when applicable.
4. **Mechanics and free inputs**: duration, action cost, free claims, queues or teams, reset and carryover rules, current progress, and any state that changes future rewards.

Accept clear in-game screenshots, exact user transcriptions, or explicit user confirmation that a candidate source version matches the current game. Use KingshotPacks `ages` and Kingshot Mastery unlock or kingdom-age notes only to select candidate variants; never treat them as confirmation by themselves.

If any value-affecting field remains unconfirmed, return a concise missing-input checklist and stop before scaffolding or calculating. Set the model verification flags to `true` only after the user or in-game evidence confirms the applicable variant.

## Workflow

1. Research current activity mechanics with `$kingshot-event-data`. Record the direct page URL, visible update date, event duration, unlock conditions, scoring or action rules, milestones, and every version caveat.
2. Query event packs with `$kingshot-packs-data`. Compare every returned `ages` or content variant with the player's server context.
3. Build a verification matrix for the four mandatory groups. Treat the user's current in-game screens as authoritative and record every website mismatch. Stop and request only the missing confirmations when the gate is incomplete.
4. Refresh `$kingshot-value-calc` once after the gate passes. Map every confirmed reward to an exact Builder item and preserve its named unit. Leave unresolved items unvalued; never assign them zero silently.
5. If the target already has `event-models/<event-slug>.md`, read it as activity-specific model notes. Reconcile it with current in-game data; never apply its mechanics to another event.
6. Scaffold the report and its companion files only after the verification gate passes:

   ```powershell
   uv run python <skill-dir>\scripts\scaffold_event_report.py --event-name "逐風之旅" --slug windward-voyage --output-dir <target-dir>
   ```

7. Read [references/modeling-guide.md](references/modeling-guide.md), choose the event's model type, and replace the scaffolded JSON and calculation script with the verified rules.
8. Run the event-specific calculation script. Generate every displayed result from its output rather than retyping arithmetic into Markdown.
9. Fill the scaffolded report. Keep confirmed inputs, assumptions, formulas, results, and recommendations in separate sections.
10. Validate the final artifact:

   ```powershell
   uv run python <skill-dir>\scripts\validate_event_report.py <report.md> --strict
   ```

11. Re-run the calculation and validator after any rule, quantity, price, probability, purchase cap, progress, or valuation change.

## Required Artifacts

Create all three in the user's target directory:

```text
Kingshot-<中文活動名稱>-CP值報告.md
data/<event-slug>.json
scripts/calculate-<event-slug>.py
```

- Store source-backed facts, user-confirmed in-game data, assumptions, unresolved fields, packs, rewards, and milestones in the JSON.
- Record the server context, confirmation evidence, and all four verification flags in the JSON.
- Keep activity-specific state transitions, probability distributions, enumeration, and optimization in the calculation script.
- Link both companion files from the report with working relative paths.
- Use the filename pattern exactly unless the user requests another name.

## Accounting Boundaries

- Calculate the player's confirmed current state with all already-owned resources, unlocked queues or teams, already-purchased packs, claimed rewards, partial progress, active timers, and remaining purchase caps. Advance that state to event end with **no additional purchases** and call the result the `當下免費基準`.
- Default every headline recommendation, milestone plan, and main CP column to **marginal CP from the same current state**. Treat all earlier payments and rewards as sunk history: exclude them from both the numerator and denominator of a new purchase decision.
- Value a purchase as its direct included items plus the incremental event outcome:

  ```text
  marginal_value(new_purchases, current_state)
  = direct_value(new_purchases)
  + expected_event_reward_value(state_after_new_purchases)
  - expected_event_reward_value(current_state_with_no_new_purchase)

  marginal_cp
  = marginal_value_usd / new_cash_paid_usd
  ```

- Do not give compasses, pickaxes, energy, tickets, dice, or similar event currencies an arbitrary direct Gem value when they are consumed to produce modeled rewards. Value either the currency or its resulting actions and rewards, never both.
- Do not charge paid purchases for rewards already reachable from free progress. Let free resources affect paid value only through the exact incremental state difference, including newly crossed milestones.
- Recalculate the no-additional-purchase baseline after every mid-event progress update. Never use current progress alone as the baseline when owned resources or natural production can still earn more rewards.
- Enforce remaining purchase caps after subtracting already-purchased quantities. Optimize only legal new purchases; never include an already-purchased pack in `new_cash_paid_usd` or `direct_value(new_purchases)`.
- If the no-additional-purchase baseline already reaches a target, report `無需加買`, `US$0`, and CP `—`. Never report zero, infinity, or attribute the free result to a pack.
- Report `single-pack marginal CP at the current baseline` separately from `marginal CP after a selected prior purchase`. A pack can cross a milestone in one state but not another.
- Show historical, cumulative-bundle, or all-in-event CP only when explicitly useful or requested. Label it `累積 CP` or `全成本 CP`, keep it out of the main CP column, and never substitute it for marginal CP in the recommendation.
- Separate pack-only CP from all-in event CP when unlocking queues, teams, passes, or other prerequisites costs Gems.
- Treat mutually exclusive reward choices as alternatives. Value the selected option or show a sensitivity range.
- For random outcomes, calculate expected value from the full distribution. Use exact enumeration or dynamic programming when feasible; otherwise disclose the simulation seed, trial count, error estimate, and guarantees.
- Keep milestone rewards separate from repeatable action rewards so neither is counted twice.

## Purchase Optimization

- Record whether tiers are independent, sequential, daily-reset, event-limited, or prerequisite-gated.
- Enumerate all legal integer combinations within the confirmed caps. Do not assume tiers must be bought in order.
- For each milestone, report the cheapest qualifying **additional** combination, resulting progress, new cash cost, marginal CP, and safety buffer from the same current-state baseline.
- Use these main decision-table columns by default: `目標進度`, `追加禮包方案`, `購買後實際進度`, `追加現金`, `邊際 CP`. Add a safety-buffer column when timing or randomness matters.
- When comparing sequential upgrades, use a separate table and calculate each step from the state after the preceding selected plan. Do not subtract one independently optimized target plan from another when their pack quantities are not nested.
- Provide a realistic buffered alternative when the cheapest plan depends on uninterrupted play, exact timing, or favorable randomness.
- Rank plans by the user's objective: cheapest guarantee, highest expected CP, target milestone, or progression bottleneck. Do not substitute one objective for another.

## Report Rules

- Use Traditional Chinese unless the user requests another language; preserve the English event name alongside its Chinese name when confirmed.
- Include the data date and live/cache/fallback status for all refreshed sources.
- Include a server-variant verification table. State who or what confirmed the pack and reward contents and when.
- Keep exact USD prices and quantities during calculations. Round only displayed values.
- In the summary, state the current no-additional-purchase outcome before any paid recommendation and call every headline CP number `邊際 CP`.
- Explain why neighboring pack tiers have different CP, especially when a milestone crossing changes the result.
- Include sensitivity analysis for uncertain or user-adjusted item values, probabilities, play uptime, purchase limits, or reward choices.
- List every unresolved input and state which conclusions remain valid without it.
- Do not call the report complete until its calculation script runs successfully and `validate_event_report.py --strict` passes.

Use [assets/event-report-template.md](assets/event-report-template.md) as the report structure. Copy and fill it through the scaffold script instead of editing the asset itself.
