from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

from glossary_store import (
    DEFAULT_BASE_GLOSSARY,
    assert_aliases_available,
    default_user_glossary,
    load_layers,
    locate_pair,
    merge_glossaries,
    unique,
    write_atomic,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def upsert_term(
    base: dict,
    user: dict,
    merged: dict,
    args: argparse.Namespace,
) -> str:
    missing_sources = [
        source_id for source_id in args.source_id if source_id not in merged["sources"]
    ]
    if missing_sources:
        raise ValueError(
            "Add source metadata before learning this pair. Unknown source IDs: "
            + ", ".join(missing_sources)
        )

    terms = merged["terms"]
    current = locate_pair(terms, args.zh_tw, args.en)
    aliases_zh = unique(args.alias_zh_tw)
    aliases_en = unique(args.alias_en)
    assert_aliases_available(terms, current, aliases_zh, "zh")
    assert_aliases_available(terms, current, aliases_en, "en")
    effective_date = args.verified_at or date.today().isoformat()

    if current is None:
        proposed = {
            "zhTw": args.zh_tw,
            "en": args.en,
            "category": args.category,
            "aliasesZhTw": aliases_zh,
            "aliasesEn": aliases_en,
            "status": "confirmed",
            "verifiedAt": effective_date,
            "sourceIds": unique(args.source_id),
        }
        if args.notes:
            proposed["notes"] = args.notes
        user["terms"].append(proposed)
        action = "created"
    else:
        if current["category"] != args.category:
            raise ValueError(
                f"Category conflict: existing {current['category']!r}, received {args.category!r}. "
                "Ask the user before changing it."
            )
        if args.notes and current.get("notes") not in (None, args.notes):
            raise ValueError("Notes conflict. Preserve the existing note and ask the user before replacing it.")

        proposed = deepcopy(current)
        proposed["aliasesZhTw"] = unique([*current.get("aliasesZhTw", []), *aliases_zh])
        proposed["aliasesEn"] = unique([*current.get("aliasesEn", []), *aliases_en])
        proposed["sourceIds"] = unique([*current.get("sourceIds", []), *args.source_id])
        if args.notes and "notes" not in proposed:
            proposed["notes"] = args.notes
        if args.verified_at and proposed.get("verifiedAt") != args.verified_at:
            proposed["verifiedAt"] = args.verified_at

        if proposed == current:
            return "unchanged"

        proposed["verifiedAt"] = effective_date
        user_current = locate_pair(user["terms"], current["zhTw"], current["en"])
        if user_current is None:
            user["terms"].append(proposed)
        else:
            user_current.clear()
            user_current.update(proposed)
        action = "updated"

    user["updatedAt"] = effective_date
    merge_glossaries(base, user)
    return action


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely add or enrich a user-confirmed Kingshot Chinese-English translation pair."
    )
    parser.add_argument("--zh-tw", required=True, help="Canonical Traditional Chinese name")
    parser.add_argument("--en", required=True, help="Canonical English name")
    parser.add_argument("--category", required=True, help="Exact item category")
    parser.add_argument("--source-id", action="append", required=True, help="Existing merged glossary source ID")
    parser.add_argument("--alias-zh-tw", action="append", default=[], help="Confirmed Traditional Chinese alias")
    parser.add_argument("--alias-en", action="append", default=[], help="Confirmed English alias")
    parser.add_argument("--notes", help="Non-conflicting distinction or context")
    parser.add_argument(
        "--verified-at",
        help="Verification date in YYYY-MM-DD; defaults to today for a created or enriched term",
    )
    parser.add_argument("--base-glossary", type=Path, default=DEFAULT_BASE_GLOSSARY)
    parser.add_argument("--user-glossary", type=Path, default=default_user_glossary())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        base, user, merged = load_layers(args.base_glossary, args.user_glossary)
        action = upsert_term(base, user, merged, args)
        if action != "unchanged" and not args.dry_run:
            write_atomic(args.user_glossary, user)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    mode = "dry-run" if args.dry_run else ("not-written" if action == "unchanged" else "written")
    print(f"{action}: {args.zh_tw} <-> {args.en} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
