# Transfer research and report method

## Live KS Atlas entry points

- `https://ks-atlas.com/` — kingdom directory and profiles.
- `https://ks-atlas.com/rankings` — kingdom Mystic comparison.
- `https://ks-atlas.com/rankings/player-rankings` — transfer-group player ranking.
- `https://ks-atlas.com/transfer-hub` — visible recruitment information.
- `https://ks-atlas.com/kingdom/<number>` — individual kingdom details.

KS Atlas is unofficial and its public page/API schema can change. Verify the current page, network response, labels, and snapshot dates for every investigation.

## Metric boundaries

| Metric | Useful for | Do not claim |
|---|---|---|
| Power | Broad account combat strength and whale size | Exact activity performance, command skill, or attendance |
| Mystic | Mystic Trial progression and high-end development density | Total Power or nationality |
| Mystic Top 5/20 | Front-line strength and leaderboard pressure | Whole-kingdom activity or morale |
| Mystic Top 100 total | Developed-player depth | Total population |
| KvK preparation/battle records | Recent results | Long-term stability from only a few matches |
| Atlas Score | Site-defined comparison | An official Kingshot tier |

## Normalized player CSV

Required fields:

```text
kingdom,local_mystic_rank,player,mystic,power,
judgment_code,judgment,confidence,reason,direct_chinese_name,snapshot_date
```

Optional fields:

```text
transfer_group_rank,high_end_scope,alliance,source_url,source_snapshot_at,
governor_id,tracker_uid,known_names,id_match_status,id_source,id_last_checked
```

Store Power and Mystic as unrounded numbers. Round only report display values. Keep the original player spelling and Unicode.

`governor_id` is the in-game Governor/Player ID and is the durable identity key. `tracker_uid` is an optional third-party database key; never treat it as the Governor ID. Rankings, kingdom numbers, Power values, and trailing notes such as an old rank are not IDs. When `governor_id` is present, record the match status, source, last-check date, and previous visible names. Read [player-id-registry.md](player-id-registry.md) for the registry contract.

## Recommended comparison angles

Keep these as separate facts or tables; do not collapse everything into one unexplained score:

1. Direct Chinese/Taiwan player-name count.
2. Direct-name players in each kingdom's Mystic Top 20.
3. Direct-name players in the transfer-group Top 100.
4. Highest Power and highest Mystic direct-name players.
5. Kingdom Mystic front-line and Top 100 depth.
6. Recent KvK preparation and battle record, with sample size.
7. Expected leaderboard pressure.
8. Public recruitment, UTC+8 event times, NAP, castle rotation, and reward policy—confirmed outside name inference.

## Player ranking

Use `scripts/rank_players.py` after the audit.

- `--sort-by power`: Power descending; equal Power shares a rank, with Mystic descending within the tie.
- `--sort-by mystic`: Mystic descending; equal Mystic shares a rank, with Power descending within the tie.
- Direct rows only are included by default.
- Preserve a row number in addition to the competition rank.

## Report shape

Use only sections relevant to the request:

1. Outcome-first recommendations by user objective.
2. Data range, transfer group, lookup date, and snapshot caveats.
3. Power versus Mystic explanation.
4. Complete requested player ranking.
5. Per-kingdom player-name coverage.
6. Optional KvK/Mystic comparison when requested.
7. Migration verification checklist.
8. Direct source links and local reproducibility artifacts.

Do not infer a Chinese community from an alliance name when the user asked for player-name analysis. Do not turn the current report's preferred sections into a permanent requirement; follow the user's requested inclusions and omissions.
