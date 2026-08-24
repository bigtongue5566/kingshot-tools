from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

from glossary_store import (
    DEFAULT_BASE_GLOSSARY,
    default_user_glossary,
    load_layers,
    merge_glossaries,
    write_atomic,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def requested_metadata(args: argparse.Namespace) -> dict[str, str]:
    values = {
        "type": args.type,
        "url": args.url,
        "date": args.date,
        "fetchedAt": args.fetched_at,
        "path": args.path,
        "context": args.context,
    }
    return {key: value for key, value in values.items() if value is not None}


def upsert_source(
    base: dict,
    user: dict,
    merged: dict,
    *,
    source_id: str,
    metadata: dict[str, str],
    updated_at: str,
) -> str:
    existing = merged["sources"].get(source_id)
    proposed = deepcopy(existing) if existing is not None else {}
    for field, value in metadata.items():
        if field in proposed and proposed[field] != value:
            raise ValueError(
                f"Source conflict for {source_id!r} field {field!r}. Ask the user before replacing it."
            )
        proposed[field] = value

    if existing == proposed:
        return "unchanged"

    user["sources"][source_id] = proposed
    user["updatedAt"] = updated_at
    merge_glossaries(base, user)
    return "created" if existing is None else "updated"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely add or enrich a source in the persistent Kingshot user glossary."
    )
    parser.add_argument("--source-id", required=True, help="Stable source identifier")
    parser.add_argument("--type", required=True, help="Evidence source type")
    parser.add_argument("--url")
    parser.add_argument("--date")
    parser.add_argument("--fetched-at")
    parser.add_argument("--path")
    parser.add_argument("--context")
    parser.add_argument("--updated-at", default=date.today().isoformat(), help="Update date in YYYY-MM-DD")
    parser.add_argument("--base-glossary", type=Path, default=DEFAULT_BASE_GLOSSARY)
    parser.add_argument("--user-glossary", type=Path, default=default_user_glossary())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        base, user, merged = load_layers(args.base_glossary, args.user_glossary)
        action = upsert_source(
            base,
            user,
            merged,
            source_id=args.source_id,
            metadata=requested_metadata(args),
            updated_at=args.updated_at,
        )
        if action != "unchanged" and not args.dry_run:
            write_atomic(args.user_glossary, user)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    mode = "dry-run" if args.dry_run else ("not-written" if action == "unchanged" else "written")
    print(f"{action}: source {args.source_id} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
