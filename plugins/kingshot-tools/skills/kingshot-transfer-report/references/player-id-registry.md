# Player ID registry

Use this reference when the user wants to identify the same Kingshot account after a player changes their visible name.

## Identity boundary

- Use the in-game `Governor ID` / `Player ID` as the primary key. Store it as `governor_id`.
- Treat `tracker_uid` as a separate third-party database key. It must never replace or be presented as the in-game ID.
- Names, kingdom numbers, alliance tags, Power, Mystic, and leaderboard ranks can all change or be ambiguous. They are matching evidence, not identity keys.
- Public leaderboards may omit the in-game ID. Leave `governor_id` blank until there is a defensible match; never manufacture one from another number.
- Prefer an ID copied from the player's in-game profile. A third-party exact-name/kingdom lookup is useful for a candidate match but remains pending until checked in game or against another independent source.

## Registry CSV

Use one current row per `governor_id` with these columns:

```text
governor_id,tracker_uid,current_kingdom,current_name,known_names,
provided_label,rank_hint,match_status,id_source,id_last_checked,notes
```

- `known_names`: prior exact visible names separated by ` | `; preserve Unicode and spelling.
- `provided_label`: the shorthand or spelling originally supplied by the user.
- `rank_hint`: an explicitly labeled historical rank only. Never reinterpret it as an ID.
- `match_status`: distinguish at least `in_game_confirmed`, `third_party_exact_pending`, `high_confidence_candidate`, and `unresolved_candidate`.
- `id_source`: state where the ID came from; do not imply KS Atlas supplied it when another service did.
- `id_last_checked`: ISO date (`YYYY-MM-DD`) for the identity lookup, not the leaderboard snapshot date.

Use `scripts/upsert_player_registry.py` to update a row. If the current visible name changes, the script moves the former current name into `known_names` before writing the new name. Review candidates manually before upgrading their status to `in_game_confirmed`.

## Report display

Keep the registry as reproducible source data. Add IDs to a public report only when the user asks for them and understands that the report will expose a persistent account identifier. Otherwise use the ID internally for deduplication while displaying the current name and, when useful, a compact former-name note.
