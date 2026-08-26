#!/usr/bin/env python3
"""以必要欄位查詢 Kingshot Stats 玩家與王國資料。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PUBLIC_BASE = "https://www.kingshotstats.com"
API_BASE = "https://api.kingshotstats.com/v1"
USER_AGENT = "kingshot-tools/0.1 kingshot-stats-data"


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必須是正整數") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("必須是正整數")
    return number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    player = subparsers.add_parser("player", help="依遊戲內 Governor ID 查詢玩家")
    player.add_argument("governor_id", type=positive_int)
    player.add_argument("--live", action="store_true", help="要求公開網站進行即時查詢")
    player.add_argument("--output", type=Path, help="將標準化 JSON 寫入檔案")

    search = subparsers.add_parser("search", help="依名稱或文字搜尋玩家")
    search.add_argument("query")
    search.add_argument("--limit", type=positive_int, default=20)
    search.add_argument("--live", action="store_true", help="要求公開網站進行即時查詢")
    search.add_argument("--exact-name", action="store_true", help="只保留名稱完全相同的結果")
    add_range_options(search, optional=True)
    search.add_argument("--output", type=Path, help="將標準化 JSON 寫入檔案")

    kingdom = subparsers.add_parser("kingdom", help="取得王國公開玩家名冊")
    kingdom.add_argument("kingdom", type=positive_int)
    kingdom.add_argument("--players", type=positive_int, default=200)
    kingdom.add_argument("--name-contains", help="只保留名稱包含指定文字的玩家")
    kingdom.add_argument("--exact-name", action="store_true", help="名稱篩選改為完全相同")
    kingdom.add_argument("--output", type=Path, help="將標準化 JSON 寫入檔案")

    range_name = subparsers.add_parser("range-name", help="掃描王國區間內含指定名稱的玩家")
    range_name.add_argument("query")
    add_range_options(range_name, optional=False)
    range_name.add_argument("--players", type=positive_int, default=200)
    range_name.add_argument("--workers", type=positive_int, default=8)
    range_name.add_argument("--exact-name", action="store_true", help="只保留名稱完全相同的結果")
    range_name.add_argument("--output", type=Path, help="將標準化 JSON 寫入檔案")

    api_player = subparsers.add_parser("api-player", help="使用需金鑰的正式 API 查詢玩家")
    api_player.add_argument("governor_id", type=positive_int)
    api_player.add_argument("--include", default="base,ranks")
    api_player.add_argument("--api-key-env", default="KINGSHOT_STATS_API_KEY")
    api_player.add_argument("--output", type=Path, help="將標準化 JSON 寫入檔案")

    api_ranks = subparsers.add_parser("api-kingdom-ranks", help="使用正式 API 查王國排行榜")
    api_ranks.add_argument("kingdom", type=positive_int)
    api_ranks.add_argument("--board", default="mystic_trial")
    api_ranks.add_argument("--limit", type=positive_int, default=100)
    api_ranks.add_argument("--api-key-env", default="KINGSHOT_STATS_API_KEY")
    api_ranks.add_argument("--output", type=Path, help="將標準化 JSON 寫入檔案")
    return parser.parse_args()


def add_range_options(parser: argparse.ArgumentParser, *, optional: bool) -> None:
    parser.add_argument("--min-kingdom", type=positive_int, required=not optional)
    parser.add_argument("--max-kingdom", type=positive_int, required=not optional)


def request_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    request_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    request_headers.update(headers or {})
    last_error = "未知錯誤"
    for attempt in range(retries + 1):
        try:
            with urlopen(Request(url, headers=request_headers), timeout=35) as response:
                payload = json.load(response)
            if isinstance(payload, dict) and payload.get("ok") is False:
                last_error = str(payload.get("error") or "服務回傳失敗")
                if last_error == "busy" and attempt < retries:
                    time.sleep(0.6 * (attempt + 1))
                    continue
                raise RuntimeError(last_error)
            if not isinstance(payload, dict):
                raise RuntimeError("服務回傳的 JSON 不是物件")
            return payload
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {body[:300]}"
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries:
                time.sleep(0.6 * (attempt + 1))
                continue
        except (URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = str(exc)
            if attempt < retries and ("busy" in last_error.lower() or isinstance(exc, (URLError, TimeoutError))):
                time.sleep(0.6 * (attempt + 1))
                continue
            break
    raise RuntimeError(last_error)


def normalize_player(row: dict[str, Any]) -> dict[str, Any]:
    alliance = row.get("alliance") if isinstance(row.get("alliance"), dict) else {}
    return {
        "governor_id": row.get("governor_id") or row.get("fid"),
        "tracker_uid": row.get("uid"),
        "name": row.get("nick_name") or row.get("name"),
        "kingdom": row.get("kid") or row.get("kingdom"),
        "alliance_abbr": row.get("alliance_abbr") or alliance.get("abbr"),
        "alliance_name": row.get("alliance_name") or alliance.get("name"),
        "power": row.get("power"),
        "mystic": row.get("mystic_trial") or row.get("mystic"),
        "power_rank": row.get("power_rank") or row.get("rank"),
        "mystic_rank": row.get("mystic_rank"),
        "last_active_at": row.get("last_active_at"),
        "last_login": row.get("last_login") or row.get("last_active_label"),
        "from_live": bool(row.get("from_live", False)),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def public_search_url(query: str, limit: int, live: bool) -> str:
    params = urlencode({"q": query, "limit": limit, "live": 1 if live else 0})
    return f"{PUBLIC_BASE}/api/search?{params}"


def public_kingdom_url(kingdom: int, players: int) -> str:
    return f"{PUBLIC_BASE}/api/kingdoms/{kingdom}?players={players}&alliances=1"


def validate_range(min_kingdom: int | None, max_kingdom: int | None) -> None:
    if (min_kingdom is None) != (max_kingdom is None):
        raise SystemExit("--min-kingdom 與 --max-kingdom 必須一起提供")
    if min_kingdom is not None and min_kingdom > max_kingdom:
        raise SystemExit("--min-kingdom 不可大於 --max-kingdom")


def name_matches(name: Any, query: str, exact: bool) -> bool:
    text = str(name or "")
    return text.casefold() == query.casefold() if exact else query.casefold() in text.casefold()


def base_output(action: str, source_url: str) -> dict[str, Any]:
    return {
        "action": action,
        "queried_at": now_iso(),
        "source_url": source_url,
        "complete": True,
        "results": [],
        "errors": [],
    }


def run_player(args: argparse.Namespace) -> dict[str, Any]:
    url = public_search_url(str(args.governor_id), 20, args.live)
    payload = request_json(url)
    exact = [
        row
        for row in payload.get("results", [])
        if str(row.get("fid") or row.get("governor_id")) == str(args.governor_id)
    ]
    output = base_output("player", url)
    output["live_requested"] = args.live
    output["service_live"] = payload.get("live")
    output["results"] = [normalize_player(row) for row in exact]
    if not exact:
        output["complete"] = False
        output["errors"].append("沒有找到完全相同的 Governor ID")
    return output


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    validate_range(args.min_kingdom, args.max_kingdom)
    url = public_search_url(args.query, args.limit, args.live)
    payload = request_json(url)
    rows = list(payload.get("results", []))
    if args.exact_name:
        rows = [row for row in rows if name_matches(row.get("nick_name"), args.query, True)]
    if args.min_kingdom is not None:
        rows = [
            row
            for row in rows
            if args.min_kingdom <= int(row.get("kid") or 0) <= args.max_kingdom
        ]
    output = base_output("search", url)
    output["live_requested"] = args.live
    output["service_live"] = payload.get("live")
    output["results"] = [normalize_player(row) for row in rows]
    return output


def extract_kingdom_players(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("players"), list):
        return payload["players"]
    kingdom = payload.get("kingdom")
    if isinstance(kingdom, dict) and isinstance(kingdom.get("players"), list):
        return kingdom["players"]
    return []


def run_kingdom(args: argparse.Namespace) -> dict[str, Any]:
    url = public_kingdom_url(args.kingdom, args.players)
    payload = request_json(url)
    rows = extract_kingdom_players(payload)
    if args.name_contains:
        rows = [
            row
            for row in rows
            if name_matches(row.get("nick_name"), args.name_contains, args.exact_name)
        ]
    output = base_output("kingdom", url)
    output["kingdom"] = args.kingdom
    output["results"] = [normalize_player(row) for row in rows]
    return output


def scan_one_kingdom(kingdom: int, players: int, query: str, exact: bool) -> tuple[int, str, list[dict[str, Any]]]:
    url = public_kingdom_url(kingdom, players)
    payload = request_json(url)
    rows = [
        normalize_player(row)
        for row in extract_kingdom_players(payload)
        if name_matches(row.get("nick_name"), query, exact)
    ]
    return kingdom, url, rows


def run_range_name(args: argparse.Namespace) -> dict[str, Any]:
    validate_range(args.min_kingdom, args.max_kingdom)
    kingdoms = list(range(args.min_kingdom, args.max_kingdom + 1))
    output = base_output(
        "range-name",
        f"{PUBLIC_BASE}/api/kingdoms/<K>?players={args.players}&alliances=1",
    )
    output["requested_range"] = [args.min_kingdom, args.max_kingdom]
    output["scanned_kingdoms"] = []
    with ThreadPoolExecutor(max_workers=min(args.workers, 8)) as executor:
        futures = {
            executor.submit(scan_one_kingdom, kingdom, args.players, args.query, args.exact_name): kingdom
            for kingdom in kingdoms
        }
        for future in as_completed(futures):
            kingdom = futures[future]
            try:
                scanned, _, rows = future.result()
                output["scanned_kingdoms"].append(scanned)
                output["results"].extend(rows)
            except Exception as exc:  # noqa: BLE001 - 逐國保留錯誤
                output["complete"] = False
                output["errors"].append({"kingdom": kingdom, "error": str(exc)})
    output["scanned_kingdoms"].sort()
    output["results"].sort(key=lambda row: (int(row.get("kingdom") or 0), -(row.get("power") or 0)))
    return output


def api_headers(env_name: str) -> dict[str, str]:
    api_key = os.environ.get(env_name, "").strip()
    if not api_key:
        raise SystemExit(f"找不到環境變數 {env_name}；請先設定 Kingshot Stats API key")
    return {"Authorization": f"Bearer {api_key}"}


def run_api_player(args: argparse.Namespace) -> dict[str, Any]:
    url = f"{API_BASE}/players/{args.governor_id}?{urlencode({'include': args.include})}"
    payload = request_json(url, headers=api_headers(args.api_key_env))
    player = dict(payload.get("player", {}))
    ranks = payload.get("ranks")
    if isinstance(ranks, dict):
        for field in ("power_rank", "mystic_trial", "mystic_rank"):
            if player.get(field) is None and ranks.get(field) is not None:
                player[field] = ranks[field]
    output = base_output("api-player", url)
    output.update(
        {
            "fresh": payload.get("fresh"),
            "cached_at": payload.get("cached_at"),
            "age_seconds": payload.get("age_seconds"),
            "results": [normalize_player(player)] if player else [],
        }
    )
    if not player:
        output["complete"] = False
        output["errors"].append("正式 API 沒有回傳 player 物件")
    return output


def run_api_kingdom_ranks(args: argparse.Namespace) -> dict[str, Any]:
    params = urlencode({"board": args.board, "limit": args.limit})
    url = f"{API_BASE}/kingdoms/{args.kingdom}/ranks?{params}"
    payload = request_json(url, headers=api_headers(args.api_key_env))
    output = base_output("api-kingdom-ranks", url)
    rows = payload.get("rows") or payload.get("ranking") or payload.get("ranks") or []
    normalized_rows = []
    for source_row in rows:
        row = dict(source_row)
        if args.board == "mystic_trial" and row.get("mystic_trial") is None:
            row["mystic_trial"] = row.get("score")
        if args.board == "personal_power" and row.get("power") is None:
            row["power"] = row.get("score")
        normalized_rows.append(normalize_player(row))
    output["kingdom"] = args.kingdom
    output["board"] = args.board
    output["results"] = normalized_rows
    return output


def write_output(payload: dict[str, Any], output_path: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
        print(f"已將 {len(payload.get('results', []))} 筆結果寫入 {output_path}")
    else:
        print(text)


def main() -> int:
    args = parse_args()
    handlers = {
        "player": run_player,
        "search": run_search,
        "kingdom": run_kingdom,
        "range-name": run_range_name,
        "api-player": run_api_player,
        "api-kingdom-ranks": run_api_kingdom_ranks,
    }
    try:
        payload = handlers[args.command](args)
    except RuntimeError as exc:
        print(f"查詢失敗：{exc}", file=sys.stderr)
        return 1
    write_output(payload, args.output)
    return 0 if payload.get("complete", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())
