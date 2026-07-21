#!/usr/bin/env python3
"""
Extract pack records from KingshotPacks' live front-end bundle.

This intentionally uses only Python stdlib so it can run through `uv run python`
without installing dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


BASE_URL = "https://kingshotpacks.com"
DEFAULT_CACHE_DIR = Path(tempfile.gettempdir()) / "kingshot-packs-data"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Codex KingshotPacks data checker",
            "Accept": "text/html,application/javascript,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def js_unescape(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\\'", "'")
    try:
        return bytes(value, "utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        return value


def number_value(raw: str) -> int | float:
    if raw.lower().startswith("0x"):
        return int(raw, 16)
    if "." in raw:
        return float(raw)
    return int(raw)


def find_index_asset(page_html: str) -> str:
    candidates = re.findall(r'/(assets/index-[^"\']+\.js)', page_html)
    if not candidates:
        candidates = re.findall(r'/(assets/[^"\']+\.js)', page_html)
    if not candidates:
        raise RuntimeError("Could not find KingshotPacks JavaScript asset in page HTML")
    return f"{BASE_URL}/{candidates[0]}"


def matching_object_end(text: str, start: int) -> int:
    depth = 0
    in_string: str | None = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            continue
        if char in ("'", '"'):
            in_string = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    raise RuntimeError("Unclosed object literal while scanning KingshotPacks bundle")


def extract_object_chunks(bundle: str) -> list[str]:
    chunks: list[str] = []
    cursor = 0
    while True:
        start = bundle.find("{'name':'", cursor)
        if start == -1:
            break
        try:
            end = matching_object_end(bundle, start)
        except RuntimeError:
            cursor = start + 9
            continue
        chunk = bundle[start:end]
        if "/images/packs/" in chunk and "'priceEUR':" in chunk and "'priceUSD':" in chunk:
            chunks.append(chunk)
        cursor = start + 9
    return chunks


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def parse_ages(chunk: str) -> list[str]:
    raw = first_match(r"'ages':\[(.*?)\]", chunk)
    if not raw:
        return []
    return [js_unescape(item) for item in re.findall(r"'([^']+)'", raw)]


def parse_items(chunk: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, Any]] = set()
    pattern = re.compile(r"\{'name':'((?:\\'|[^'])+)','quantity':(0x[0-9a-fA-F]+|\d+(?:\.\d+)?)\}")
    for match in pattern.finditer(chunk):
        name = js_unescape(match.group(1))
        quantity = number_value(match.group(2))
        key = (name, quantity)
        if key in seen:
            continue
        seen.add(key)
        items.append({"name": name, "quantity": quantity})
    return items


def parse_variants(chunk: str) -> list[str]:
    variants: list[str] = []
    variant_region = first_match(r"'variants':\[(.*)\]", chunk)
    if not variant_region:
        return variants
    for match in re.finditer(r"\{'name':'((?:\\'|[^'])+)'(?:,'version':'((?:\\'|[^'])+)')?", variant_region):
        name = js_unescape(match.group(1))
        version = js_unescape(match.group(2))
        label = f"{version} - {name}" if version else name
        if label not in variants and label != "":
            variants.append(label)
    return variants


def parse_pack(chunk: str) -> dict[str, Any]:
    name = js_unescape(first_match(r"\{'name':'((?:\\'|[^'])+)'", chunk))
    return {
        "name": name,
        "priceUSD": float(first_match(r"'priceUSD':([-0-9.]+)", chunk)),
        "priceEUR": float(first_match(r"'priceEUR':([-0-9.]+)", chunk)),
        "ages": parse_ages(chunk),
        "oneTimeOnly": "'oneTimeOnly':!0x0" in chunk,
        "variants": parse_variants(chunk),
        "items": parse_items(chunk),
    }


def load_packs(cache_dir: Path, refresh: bool) -> list[dict[str, Any]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = cache_dir / "index.js"
    if refresh or not bundle_path.exists():
        page_html = fetch_text(f"{BASE_URL}/packs")
        asset_url = find_index_asset(page_html)
        bundle = fetch_text(asset_url)
        bundle_path.write_text(bundle, encoding="utf-8")
        (cache_dir / "asset_url.txt").write_text(asset_url, encoding="utf-8")
    else:
        bundle = bundle_path.read_text(encoding="utf-8")
    return [parse_pack(chunk) for chunk in extract_object_chunks(bundle)]


def matches_query(pack: dict[str, Any], queries: list[str]) -> bool:
    if not queries:
        return True
    haystack = " ".join(
        [
            pack["name"],
            " ".join(pack.get("ages", [])),
            " ".join(pack.get("variants", [])),
            " ".join(item["name"] for item in pack.get("items", [])),
        ]
    ).lower()
    return any(query.lower() in haystack for query in queries)


def format_money(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def top_items(items: list[dict[str, Any]], full_items: bool) -> str:
    selected = items if full_items else items[:6]
    rendered = ", ".join(f"{item['name']} x{item['quantity']}" for item in selected)
    if not full_items and len(items) > len(selected):
        rendered += f", +{len(items) - len(selected)} more"
    return rendered


def markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|")


def print_markdown(packs: list[dict[str, Any]], full_items: bool) -> None:
    print("| Pack | USD | EUR | Ages | One-time flag | Items |")
    print("| ---- | ---: | ---: | ---- | ------------- | ----- |")
    for pack in packs:
        ages = ", ".join(pack["ages"]) if pack["ages"] else "-"
        one_time = "yes" if pack["oneTimeOnly"] else "no"
        items = markdown_cell(top_items(pack["items"], full_items))
        print(
            f"| {markdown_cell(pack['name'])} | "
            f"${format_money(pack['priceUSD'])} | "
            f"EUR {format_money(pack['priceEUR'])} | "
            f"{markdown_cell(ages)} | {one_time} | {items} |"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Query KingshotPacks pack data")
    parser.add_argument("--query", "-q", action="append", default=[], help="Case-insensitive term to match")
    parser.add_argument("--all", action="store_true", help="Show all extracted packs")
    parser.add_argument("--limit", type=int, default=40, help="Maximum rows to print")
    parser.add_argument("--full-items", action="store_true", help="Print every extracted item")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a Markdown table")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached bundle and fetch current site data")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="Cache directory")
    args = parser.parse_args()

    if not args.query and not args.all:
        parser.error("Use --query TERM or --all")

    try:
        packs = load_packs(args.cache_dir, args.refresh)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f"Failed to fetch or parse KingshotPacks data: {error}", file=sys.stderr)
        return 2

    filtered = [pack for pack in packs if args.all or matches_query(pack, args.query)]
    filtered.sort(key=lambda pack: (pack["name"], pack["priceUSD"]))
    filtered = filtered[: args.limit]

    if args.json:
        print(json.dumps(filtered, ensure_ascii=False, indent=2))
    else:
        print_markdown(filtered, args.full_items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
