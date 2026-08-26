#!/usr/bin/env python3
"""Validate an audited Kingshot transfer-range player dataset and ranking."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any


TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"0", "false", "no", "n"}
PENDING_VALUES = {"pending", "unreviewed", "todo", "待審", "未審"}
JUDGMENT_CODES = {"T", "Z", "B", "H", "R", "J", "E", "D", "N"}
FORBIDDEN_ALLIANCE_EVIDENCE = (
    re.compile(r"(?:根據|依據|依|因|由|從|參考).{0,8}(?:聯盟|同盟|盟標|盟名)"),
    re.compile(r"(?:聯盟|同盟|盟標|盟名).{0,12}(?:判定|推斷|推測|因此|所以|台灣|中文玩家)"),
    re.compile(r"alliance\s*(?:name|tag|=|:).{0,20}(?:chinese|taiwan|tw)", re.IGNORECASE),
)
REQUIRED_FIELDS = {
    "kingdom",
    "local_mystic_rank",
    "player",
    "mystic",
    "power",
    "judgment_code",
    "judgment",
    "confidence",
    "reason",
    "direct_chinese_name",
    "snapshot_date",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("players_csv", type=Path)
    parser.add_argument("--min-kingdom", type=int, required=True)
    parser.add_argument("--max-kingdom", type=int, required=True)
    parser.add_argument("--expected-per-kingdom", type=int, default=100)
    parser.add_argument("--ranking", type=Path)
    parser.add_argument("--sort-by", choices=("power", "mystic"), default="power")
    return parser.parse_args()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def numeric(value: Any, field: str, row_number: int, errors: list[str]) -> float:
    text = str(value or "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        errors.append(f"row {row_number}: invalid {field} value {value!r}")
        return float("-inf")


def integer(value: Any, field: str, row_number: int, errors: list[str]) -> int | None:
    number = numeric(value, field, row_number, errors)
    if number == float("-inf"):
        return None
    if not number.is_integer():
        errors.append(f"row {row_number}: {field} must be an integer, got {value!r}")
        return None
    return int(number)


def is_true(value: Any) -> bool:
    return str(value or "").strip().lower() in TRUE_VALUES


def player_key(row: dict[str, str]) -> tuple[str, ...]:
    governor_id = str(row.get("governor_id", "")).strip()
    if governor_id:
        return ("governor_id", governor_id)
    return (
        "kingdom_player",
        str(row.get("kingdom", "")).strip(),
        str(row.get("player", "")).strip(),
    )


def validate_ranking(
    ranking_path: Path,
    direct_rows: list[dict[str, str]],
    sort_by: str,
    errors: list[str],
) -> None:
    fields, ranking_rows = read_csv(ranking_path)
    rank_field = f"{sort_by}_rank"
    ranking_required = {"kingdom", "player", "power", "mystic", rank_field}
    missing = sorted(ranking_required - set(fields))
    if missing:
        errors.append(f"ranking missing required columns: {', '.join(missing)}")
        return

    expected_keys = Counter(player_key(row) for row in direct_rows)
    actual_keys = Counter(player_key(row) for row in ranking_rows)
    if expected_keys != actual_keys:
        missing_keys = sorted((expected_keys - actual_keys).elements())
        extra_keys = sorted((actual_keys - expected_keys).elements())
        if missing_keys:
            errors.append(f"ranking missing {len(missing_keys)} direct rows; first: {missing_keys[0]!r}")
        if extra_keys:
            errors.append(f"ranking has {len(extra_keys)} unexpected rows; first: {extra_keys[0]!r}")

    primary = sort_by
    secondary = "mystic" if primary == "power" else "power"
    values: list[tuple[float, float]] = []
    actual_ranks: list[int | None] = []
    for row_number, row in enumerate(ranking_rows, start=2):
        primary_value = numeric(row.get(primary), primary, row_number, errors)
        secondary_value = numeric(row.get(secondary), secondary, row_number, errors)
        actual_ranks.append(integer(row.get(rank_field), rank_field, row_number, errors))
        values.append((primary_value, secondary_value))

    for position in range(1, len(values)):
        if values[position - 1] < values[position]:
            errors.append(
                f"ranking rows {position + 1}-{position + 2} are not sorted by "
                f"descending {primary}, then {secondary}"
            )
            break

    previous_primary: float | None = None
    expected_rank = 0
    for position, ((primary_value, _), actual_rank) in enumerate(
        zip(values, actual_ranks), start=1
    ):
        if previous_primary is None or primary_value != previous_primary:
            expected_rank = position
            previous_primary = primary_value
        if actual_rank is not None and actual_rank != expected_rank:
            errors.append(
                f"ranking row {position + 1}: {rank_field} is {actual_rank}; "
                f"expected competition rank {expected_rank}"
            )


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    if args.min_kingdom > args.max_kingdom:
        errors.append("--min-kingdom cannot exceed --max-kingdom")
    if args.expected_per_kingdom < 1:
        errors.append("--expected-per-kingdom must be at least 1")

    fields, rows = read_csv(args.players_csv)
    missing_fields = sorted(REQUIRED_FIELDS - set(fields))
    if missing_fields:
        errors.append(f"dataset missing required columns: {', '.join(missing_fields)}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    counts: Counter[int] = Counter()
    keys: Counter[tuple[str, ...]] = Counter()
    local_rank_keys: Counter[tuple[int, int]] = Counter()
    direct_rows: list[dict[str, str]] = []
    for row_number, row in enumerate(rows, start=2):
        kingdom = integer(row.get("kingdom"), "kingdom", row_number, errors)
        local_rank = integer(
            row.get("local_mystic_rank"), "local_mystic_rank", row_number, errors
        )
        numeric(row.get("mystic"), "mystic", row_number, errors)
        numeric(row.get("power"), "power", row_number, errors)

        if kingdom is not None:
            counts[kingdom] += 1
            if kingdom < args.min_kingdom or kingdom > args.max_kingdom:
                errors.append(f"row {row_number}: kingdom {kingdom} is outside requested range")
            if local_rank is not None:
                local_rank_keys[(kingdom, local_rank)] += 1

        key = player_key(row)
        keys[key] += 1
        if not str(row.get("player", "")).strip():
            errors.append(f"row {row_number}: player is empty")

        governor_id = str(row.get("governor_id", "")).strip()
        tracker_uid = str(row.get("tracker_uid", "")).strip()
        if governor_id:
            if not governor_id.isdecimal() or int(governor_id) < 1:
                errors.append(f"row {row_number}: governor_id must be a positive decimal integer")
            for provenance_field in ("id_match_status", "id_source", "id_last_checked"):
                if provenance_field not in fields or not str(row.get(provenance_field, "")).strip():
                    errors.append(
                        f"row {row_number}: {provenance_field} is required when governor_id is present"
                    )
        if tracker_uid and (not tracker_uid.isdecimal() or int(tracker_uid) < 1):
            errors.append(f"row {row_number}: tracker_uid must be a positive decimal integer")

        for field in (
            "judgment_code",
            "judgment",
            "confidence",
            "reason",
            "direct_chinese_name",
            "snapshot_date",
        ):
            if not str(row.get(field, "")).strip():
                errors.append(f"row {row_number}: {field} is empty")

        judgment_code = str(row.get("judgment_code", "")).strip().upper()
        if judgment_code and judgment_code not in JUDGMENT_CODES:
            errors.append(f"row {row_number}: unknown judgment_code {judgment_code!r}")

        direct_value = str(row.get("direct_chinese_name", "")).strip().lower()
        if direct_value not in TRUE_VALUES | FALSE_VALUES:
            errors.append(
                f"row {row_number}: direct_chinese_name must be an explicit boolean, "
                f"got {row.get('direct_chinese_name')!r}"
            )

        if "review_status" in fields:
            review_status = str(row.get("review_status", "")).strip().lower()
            if review_status in PENDING_VALUES:
                errors.append(f"row {row_number}: review_status is still {review_status!r}")

        if is_true(row.get("direct_chinese_name")):
            direct_rows.append(row)
            reason = str(row.get("reason", ""))
            if any(pattern.search(reason) for pattern in FORBIDDEN_ALLIANCE_EVIDENCE):
                errors.append(
                    f"row {row_number}: direct judgment reason appears to infer from alliance evidence"
                )

    duplicate_keys = [key for key, count in keys.items() if count > 1]
    if duplicate_keys:
        errors.append(f"duplicate player identities: {len(duplicate_keys)}; first: {duplicate_keys[0]!r}")

    duplicate_local_ranks = [key for key, count in local_rank_keys.items() if count > 1]
    if duplicate_local_ranks:
        errors.append(
            f"duplicate kingdom/local_mystic_rank rows: {len(duplicate_local_ranks)}; "
            f"first: {duplicate_local_ranks[0]!r}"
        )

    expected_kingdoms = range(args.min_kingdom, args.max_kingdom + 1)
    for kingdom in expected_kingdoms:
        if counts[kingdom] != args.expected_per_kingdom:
            errors.append(
                f"K{kingdom} has {counts[kingdom]} rows; expected {args.expected_per_kingdom}"
            )

    if args.ranking:
        validate_ranking(args.ranking, direct_rows, args.sort_by, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1

    print(
        f"Validated {len(rows)} rows across {len(counts)} kingdoms; "
        f"{len(direct_rows)} direct Chinese-name rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
