#!/usr/bin/env python3
"""Fetch KingshotPacks Builder item values and calculate pack CP value."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Iterable


BASE_URL = "https://kingshotpacks.com"
BUILDER_URL = f"{BASE_URL}/builder"
WEBSITE_FALLBACK_USD_PER_1000_GEMS = Decimal("1.98")
DEFAULT_CACHE_DIR = Path(tempfile.gettempdir()) / "kingshot-value-calc"

ITEM_PATTERN = re.compile(
    r"\{'name':'((?:\\.|[^'])+)',"
    r"'gemCost':(0x[0-9a-fA-F]+|\d+(?:\.\d+)?),"
    r"'image':'((?:\\.|[^'])+)',"
    r"'category':'((?:\\.|[^'])+)',"
    r"'itemType':'((?:\\.|[^'])+)'"
    r"(?:,'amount':(0x[0-9a-fA-F]+|\d+(?:\.\d+)?))?\}"
)

TOP_UP_TIER_PATTERN = re.compile(
    r"\{'gems':(0x[0-9a-fA-F]+|\d+(?:\.\d+)?),"
    r"'priceEUR':(0x[0-9a-fA-F]+|\d+(?:\.\d+)?),"
    r"'priceUSD':(0x[0-9a-fA-F]+|\d+(?:\.\d+)?)\}"
)

RAW_ALIASES = {
    "鑽石": "Gems",
    "寶石": "Gems",
    "100鑽石": "100 Gems",
    "1000鑽石": "1000 Gems",
    "8小時通用加速": "8 Hour Speedup",
    "3小時通用加速": "3 Hour Speedup",
    "1小時通用加速": "1 Hour Speedup",
    "5分鐘通用加速": "5 Minute Speedup",
    "1分鐘通用加速": "1 Minute Speedup",
    "1小時建築加速": "1 Hour Construction Speedup",
    "5分鐘建築加速": "5 Minute Construction Speedup",
    "1小時建造加速": "1 Hour Construction Speedup",
    "5分鐘建造加速": "5 Minute Construction Speedup",
    "1小時訓練加速": "1 Hour Training Speedup",
    "5分鐘訓練加速": "5 Minute Training Speedup",
    "1小時研究加速": "1 Hour Research Speedup",
    "5分鐘研究加速": "5 Minute Research Speedup",
    "1小時治療加速": "1 Hour Healing Speedup",
    "5分鐘治療加速": "5 Minute Healing Speedup",
    "10體力": "10 Stamina",
    "金幣": "Gold",
    "1k石材": "1k Stone",
    "10k石材": "10k Stone",
    "100k石材": "100k Stone",
    "1k鐵礦": "1k Iron",
    "10k鐵礦": "10k Iron",
    "100k鐵礦": "100k Iron",
    "10k糧食": "10k Food",
    "100k糧食": "100k Food",
    "10k木材": "10k Wood",
    "100k木材": "100k Wood",
    "10vip經驗": "10 VIP XP",
    "100vip經驗": "100 VIP XP",
    "1000vip經驗": "1000 VIP XP",
    "10000vip經驗": "10000 VIP XP",
    "1k英雄經驗": "1k Hero XP",
    "5k英雄經驗": "5k Hero XP",
    "10k英雄經驗": "10k Hero XP",
}


@dataclass(frozen=True)
class CatalogItem:
    name: str
    gem_cost: Decimal
    category: str
    item_type: str
    amount: Decimal


@dataclass(frozen=True)
class RequestedItem:
    name: str
    quantity: Decimal


def decode_js_string(value: str) -> str:
    value = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), value)
    value = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), value)
    replacements = {
        r"\'": "'",
        r'\"': '"',
        r"\n": "\n",
        r"\r": "\r",
        r"\t": "\t",
        r"\\": "\\",
    }
    for escaped, plain in replacements.items():
        value = value.replace(escaped, plain)
    return value


def parse_decimal(raw: str) -> Decimal:
    raw = raw.strip().replace(",", "")
    if raw.lower().startswith("0x"):
        return Decimal(int(raw, 16))
    try:
        return Decimal(raw)
    except InvalidOperation as error:
        raise ValueError(f"Invalid number: {raw}") from error


def decimal_arg(raw: str) -> Decimal:
    try:
        return parse_decimal(raw)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Codex Kingshot value calculator",
            "Accept": "text/html,application/javascript,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def find_asset_url(page_html: str) -> str:
    candidates = re.findall(r"(?:src=|href=)[\"']([^\"']+\.js)[\"']", page_html)
    if not candidates:
        candidates = [f"/{item}" for item in re.findall(r"/(assets/[^\"']+\.js)", page_html)]
    if not candidates:
        raise RuntimeError("Could not find a JavaScript asset on the Builder page")
    preferred = next((item for item in candidates if "/assets/index-" in item), candidates[0])
    return urllib.parse.urljoin(BUILDER_URL, preferred)


def fetch_live_bundle() -> tuple[str, str]:
    page_html = fetch_text(BUILDER_URL)
    asset_url = find_asset_url(page_html)
    return fetch_text(asset_url), asset_url


def load_bundle(
    cache_dir: Path,
    refresh: bool,
    bundle_path: Path | None,
) -> tuple[str, dict[str, str]]:
    if bundle_path is not None:
        return bundle_path.read_text(encoding="utf-8"), {
            "status": "bundle-file",
            "builder_url": BUILDER_URL,
            "bundle": str(bundle_path.resolve()),
        }

    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_bundle = cache_dir / "index.js"
    metadata_path = cache_dir / "source.json"

    if refresh or not cached_bundle.exists():
        try:
            bundle, asset_url = fetch_live_bundle()
            fetched_at = datetime.now(timezone.utc).isoformat()
            cached_bundle.write_text(bundle, encoding="utf-8")
            metadata_path.write_text(
                json.dumps(
                    {"asset_url": asset_url, "fetched_at": fetched_at},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return bundle, {
                "status": "live",
                "builder_url": BUILDER_URL,
                "asset_url": asset_url,
                "fetched_at": fetched_at,
            }
        except (urllib.error.URLError, TimeoutError, OSError, RuntimeError) as error:
            if not cached_bundle.exists():
                raise RuntimeError(f"Failed to fetch KingshotPacks Builder data: {error}") from error
            source = read_cache_metadata(metadata_path)
            source.update(
                {
                    "status": "cached-fallback",
                    "builder_url": BUILDER_URL,
                    "warning": str(error),
                }
            )
            print(
                f"Warning: live refresh failed; using cached Builder data from "
                f"{source.get('fetched_at', 'an unknown time')}: {error}",
                file=sys.stderr,
            )
            return cached_bundle.read_text(encoding="utf-8"), source

    source = read_cache_metadata(metadata_path)
    source.update({"status": "cache", "builder_url": BUILDER_URL})
    return cached_bundle.read_text(encoding="utf-8"), source


def read_cache_metadata(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def extract_catalog(bundle: str) -> list[CatalogItem]:
    by_name: dict[str, CatalogItem] = {}
    for match in ITEM_PATTERN.finditer(bundle):
        item = CatalogItem(
            name=decode_js_string(match.group(1)),
            gem_cost=parse_decimal(match.group(2)),
            category=decode_js_string(match.group(4)),
            item_type=decode_js_string(match.group(5)),
            amount=parse_decimal(match.group(6)) if match.group(6) else Decimal("1"),
        )
        existing = by_name.get(item.name)
        if existing is not None and existing != item:
            raise RuntimeError(f"Conflicting Builder records for {item.name}")
        by_name[item.name] = item
    if len(by_name) < 10:
        raise RuntimeError(
            f"Only {len(by_name)} Builder items were parsed; the front-end schema may have changed"
        )
    return sorted(by_name.values(), key=lambda item: (item.category, item.name))


def resolve_usd_per_1000_gems(
    bundle: str,
    override: Decimal | None,
) -> tuple[Decimal, dict[str, str]]:
    if override is not None:
        return override, {
            "usd_baseline_status": "user-override",
            "usd_per_1000_gems": plain_decimal(override),
        }

    for match in TOP_UP_TIER_PATTERN.finditer(bundle):
        gems = parse_decimal(match.group(1))
        if gems != Decimal("500"):
            continue
        price_usd = parse_decimal(match.group(3))
        baseline = price_usd / gems * Decimal("1000")
        return baseline, {
            "usd_baseline_status": "website-500-gem-tier",
            "usd_baseline_tier_gems": plain_decimal(gems),
            "usd_baseline_tier_price": plain_decimal(price_usd),
            "usd_per_1000_gems": plain_decimal(baseline),
        }

    return WEBSITE_FALLBACK_USD_PER_1000_GEMS, {
        "usd_baseline_status": "website-compatible-fallback",
        "usd_per_1000_gems": plain_decimal(WEBSITE_FALLBACK_USD_PER_1000_GEMS),
    }


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\s_\-:：/,，()（）]+", "", value)


def alias_map() -> dict[str, str]:
    return {normalize_name(alias): target for alias, target in RAW_ALIASES.items()}


def resolve_item(name: str, catalog: list[CatalogItem]) -> CatalogItem:
    normalized_catalog = {normalize_name(item.name): item for item in catalog}
    normalized = normalize_name(name)
    alias_target = alias_map().get(normalized)
    if alias_target is not None:
        normalized = normalize_name(alias_target)
    if normalized in normalized_catalog:
        return normalized_catalog[normalized]

    close_keys = get_close_matches(normalized, list(normalized_catalog), n=5, cutoff=0.55)
    suggestions = [normalized_catalog[key].name for key in close_keys]
    suffix = f" Suggestions: {', '.join(suggestions)}" if suggestions else ""
    raise ValueError(f"Item not found in Builder catalog: {name}.{suffix}")


def search_catalog(catalog: list[CatalogItem], queries: Iterable[str]) -> list[CatalogItem]:
    query_list = [query for query in queries if query.strip()]
    if not query_list:
        return catalog

    aliases = alias_map()
    expanded: list[str] = []
    for query in query_list:
        normalized = normalize_name(query)
        expanded.append(normalize_name(aliases.get(normalized, query)))
        expanded.extend(
            normalize_name(target)
            for alias, target in aliases.items()
            if normalized in alias
        )

    matches: list[CatalogItem] = []
    for item in catalog:
        haystack = normalize_name(f"{item.name} {item.category} {item.item_type}")
        if any(query in haystack for query in expanded):
            matches.append(item)
    return matches


def parse_item_spec(spec: str) -> RequestedItem:
    if "=" not in spec:
        raise ValueError(f"Item must use NAME=QUANTITY: {spec}")
    name, raw_quantity = spec.rsplit("=", 1)
    name = name.strip()
    if not name:
        raise ValueError(f"Item name is empty: {spec}")
    quantity = parse_decimal(raw_quantity)
    if quantity <= 0:
        raise ValueError(f"Item quantity must be greater than zero: {spec}")
    return RequestedItem(name=name, quantity=quantity)


def load_requested_items(specs: list[str], items_file: Path | None) -> list[RequestedItem]:
    requested = [parse_item_spec(spec) for spec in specs]
    if items_file is None:
        return requested

    try:
        raw_items: Any = json.loads(items_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"Could not read items JSON: {error}") from error
    if not isinstance(raw_items, list):
        raise ValueError("Items JSON must be an array")
    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict) or "name" not in raw_item or "quantity" not in raw_item:
            raise ValueError(f"Items JSON entry {index} must contain name and quantity")
        name = str(raw_item["name"]).strip()
        quantity = parse_decimal(str(raw_item["quantity"]))
        if not name or quantity <= 0:
            raise ValueError(f"Items JSON entry {index} has an invalid name or quantity")
        requested.append(RequestedItem(name=name, quantity=quantity))
    return requested


def calculate(
    paid_usd: Decimal,
    requested: list[RequestedItem],
    catalog: list[CatalogItem],
    usd_per_1000_gems: Decimal,
) -> dict[str, Any]:
    if paid_usd <= 0:
        raise ValueError("Paid USD must be greater than zero")
    if usd_per_1000_gems <= 0:
        raise ValueError("USD per 1000 Gems must be greater than zero")
    if not requested:
        raise ValueError("Provide at least one --item or --items-file entry")

    lines: list[dict[str, Any]] = []
    total_gems = Decimal("0")
    for request in requested:
        item = resolve_item(request.name, catalog)
        line_gems = item.gem_cost * request.quantity
        line_usd = line_gems / Decimal("1000") * usd_per_1000_gems
        total_gems += line_gems
        lines.append(
            {
                "input_name": request.name,
                "item": item.name,
                "quantity": request.quantity,
                "gem_cost_each": item.gem_cost,
                "gem_value": line_gems,
                "usd_value": line_usd,
            }
        )

    usd_equivalent = total_gems / Decimal("1000") * usd_per_1000_gems
    return {
        "paid_usd": paid_usd,
        "usd_per_1000_gems": usd_per_1000_gems,
        "lines": lines,
        "total_gems": total_gems,
        "usd_equivalent": usd_equivalent,
        "cp_multiplier": usd_equivalent / paid_usd,
        "gems_per_paid_usd": total_gems / paid_usd,
    }


def plain_decimal(value: Decimal) -> str:
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def rounded(value: Decimal, places: int) -> str:
    quantum = Decimal("1").scaleb(-places)
    return format(value.quantize(quantum, rounding=ROUND_HALF_UP), f".{places}f")


def print_catalog(items: list[CatalogItem], source: dict[str, str]) -> None:
    print("| Item | Gem cost | Category | Item type |")
    print("| ---- | -------: | -------- | --------- |")
    for item in items:
        print(
            f"| {item.name} | {plain_decimal(item.gem_cost)} | "
            f"{item.category} | {item.item_type} |"
        )
    print(f"\nSource: {source.get('status', 'unknown')} - {BUILDER_URL}")
    if source.get("fetched_at"):
        print(f"Fetched at: {source['fetched_at']}")


def json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return plain_decimal(value)
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    return value


def print_calculation(result: dict[str, Any], source: dict[str, str]) -> None:
    print("| Item | Quantity | Gems each | Gem subtotal | USD subtotal |")
    print("| ---- | -------: | ---------: | -----------: | -----------: |")
    for line in result["lines"]:
        print(
            f"| {line['item']} | {plain_decimal(line['quantity'])} | "
            f"{plain_decimal(line['gem_cost_each'])} | {plain_decimal(line['gem_value'])} | "
            f"${rounded(line['usd_value'], 4)} |"
        )
    print(f"\nPaid: US${rounded(result['paid_usd'], 2)}")
    print(f"Total Gem value: {plain_decimal(result['total_gems'])}")
    print(
        f"USD baseline: US${plain_decimal(result['usd_per_1000_gems'])} per 1000 Gems "
        f"({source.get('usd_baseline_status', 'unknown')})"
    )
    print(f"USD-equivalent value: US${rounded(result['usd_equivalent'], 2)}")
    print(f"CP value: {rounded(result['cp_multiplier'], 2)}x")
    print(f"Gems per paid US$1: {rounded(result['gems_per_paid_usd'], 2)}")
    print(
        f"Each US$1 buys about US${rounded(result['cp_multiplier'], 2)} "
        "of equivalent item value."
    )
    print(f"Source: {source.get('status', 'unknown')} - {BUILDER_URL}")
    if source.get("fetched_at"):
        print(f"Fetched at: {source['fetched_at']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate Kingshot pack CP value from KingshotPacks Builder gem costs"
    )
    parser.add_argument("--price-usd", type=decimal_arg, help="Actual USD price paid")
    parser.add_argument(
        "--item",
        action="append",
        default=[],
        metavar="NAME=QUANTITY",
        help="Builder item and quantity; repeat for multiple items",
    )
    parser.add_argument("--items-file", type=Path, help="UTF-8 JSON array of name/quantity objects")
    parser.add_argument("--query", action="append", default=[], help="Search the item catalog")
    parser.add_argument("--list", action="store_true", help="List the full item catalog")
    parser.add_argument("--json", action="store_true", help="Print structured JSON")
    parser.add_argument("--refresh", action="store_true", help="Fetch current Builder data")
    parser.add_argument("--bundle", type=Path, help="Read a local front-end bundle instead of fetching")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="Cache directory")
    parser.add_argument(
        "--usd-per-1000-gems",
        type=decimal_arg,
        help=(
            "Override the KingshotPacks website-derived USD value of 1000 Gems "
            "(current website value: 1.98)"
        ),
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.bundle is not None and args.refresh:
        parser.error("--bundle and --refresh cannot be used together")
    catalog_mode = args.list or bool(args.query)
    calculation_mode = args.price_usd is not None or bool(args.item) or args.items_file is not None
    if catalog_mode and calculation_mode:
        parser.error("Use catalog search/list and calculation in separate commands")
    if not catalog_mode and not calculation_mode:
        parser.error("Use --list, --query, or provide --price-usd with items")

    try:
        bundle, source = load_bundle(args.cache_dir, args.refresh, args.bundle)
        catalog = extract_catalog(bundle)
        if catalog_mode:
            matches = search_catalog(catalog, args.query) if args.query else catalog
            if args.json:
                payload = {
                    "source": source,
                    "items": [
                        {
                            "name": item.name,
                            "gem_cost": item.gem_cost,
                            "category": item.category,
                            "item_type": item.item_type,
                            "amount": item.amount,
                        }
                        for item in matches
                    ],
                }
                print(json.dumps(json_ready(payload), ensure_ascii=False, indent=2))
            else:
                print_catalog(matches, source)
            return 0

        if args.price_usd is None:
            raise ValueError("--price-usd is required for a calculation")
        requested = load_requested_items(args.item, args.items_file)
        usd_per_1000_gems, baseline_source = resolve_usd_per_1000_gems(
            bundle,
            args.usd_per_1000_gems,
        )
        source.update(baseline_source)
        result = calculate(args.price_usd, requested, catalog, usd_per_1000_gems)
        if args.json:
            print(json.dumps(json_ready({"source": source, **result}), ensure_ascii=False, indent=2))
        else:
            print_calculation(result, source)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
