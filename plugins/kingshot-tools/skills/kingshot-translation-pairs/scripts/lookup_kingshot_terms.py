from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from glossary_store import (
    DEFAULT_BASE_GLOSSARY,
    default_user_glossary,
    load_layers,
    names,
    normalize,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def find_matches(terms: list[dict[str, Any]], query: str, exact: bool) -> list[dict[str, Any]]:
    needle = normalize(query)
    if not needle:
        return []

    exact_matches = [
        term
        for term in terms
        if any(normalize(name) == needle for name in names(term, "zh") + names(term, "en"))
    ]
    if exact or exact_matches:
        return exact_matches

    return [
        term
        for term in terms
        if any(
            needle in normalize(name) or normalize(name) in needle
            for name in names(term, "zh") + names(term, "en")
        )
    ]


def resolved_sources(term: dict[str, Any], source_catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": source_id, **source_catalog[source_id]}
        for source_id in term.get("sourceIds", [])
        if source_id in source_catalog
    ]


def render_text(matches: list[dict[str, Any]], source_catalog: dict[str, Any]) -> None:
    if not matches:
        print(
            "找不到已確認的中英文配對。請先詢問使用者遊戲內的完整英文名稱、"
            "英文關鍵字或英文介面截圖，再考慮外部查詢。"
        )
        return

    for index, term in enumerate(matches, start=1):
        if len(matches) > 1:
            print(f"[{index}]")
        print(f"Traditional Chinese: {term['zhTw']}")
        print(f"English: {term['en']}")
        print(f"Category: {term['category']}")
        print(f"Status: {term['status']}")
        for source in resolved_sources(term, source_catalog):
            detail = source.get("url") or source.get("path") or source.get("context") or source.get("type")
            source_date = source.get("fetchedAt") or source.get("date") or "date unavailable"
            print(f"Source: {source['id']} | {source_date} | {detail}")
        if term.get("notes"):
            print(f"Notes: {term['notes']}")
        if index != len(matches):
            print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Look up confirmed Kingshot Traditional Chinese and English name pairs."
    )
    parser.add_argument("query", help="Traditional Chinese or English term")
    parser.add_argument("--exact", action="store_true", help="Require an exact canonical name or alias")
    parser.add_argument("--json", action="store_true", help="Return structured JSON")
    parser.add_argument(
        "--base-glossary",
        type=Path,
        default=DEFAULT_BASE_GLOSSARY,
        help="Override the read-only base glossary path",
    )
    parser.add_argument(
        "--user-glossary",
        type=Path,
        default=default_user_glossary(),
        help="Override the persistent user glossary path",
    )
    args = parser.parse_args()

    try:
        _, _, glossary = load_layers(args.base_glossary, args.user_glossary)
        matches = find_matches(glossary["terms"], args.query, args.exact)
        enriched = [
            {**term, "sources": resolved_sources(term, glossary.get("sources", {}))}
            for term in matches
        ]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        json.dump(
            {
                "query": args.query,
                "exact": args.exact,
                "baseGlossary": str(args.base_glossary),
                "userGlossary": str(args.user_glossary),
                "matches": enriched,
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        print()
    else:
        render_text(matches, glossary.get("sources", {}))

    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
