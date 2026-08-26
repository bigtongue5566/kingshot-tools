#!/usr/bin/env python3
"""依 Power 或 Mystic 排序已完成判讀的 Kingshot 玩家資料。"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


TRUE_VALUES = {"1", "true", "yes", "y"}
REQUIRED_FIELDS = {"kingdom", "player", "mystic", "power", "direct_chinese_name"}


def number(value: Any, field: str, row_number: int) -> float:
    text = str(value or "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"第 {row_number} 列：{field} 數值無效：{value!r}") from exc


def integer(value: Any, default: int = 999999) -> int:
    text = str(value or "").replace(",", "").strip()
    if not text:
        return default
    return int(float(text))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--sort-by", choices=("power", "mystic"), default="power")
    parser.add_argument(
        "--all-rows",
        action="store_true",
        help="排序所有列，不只 direct_chinese_name=true 的列",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        input_fields = list(reader.fieldnames or [])
        missing = sorted(REQUIRED_FIELDS - set(input_fields))
        if missing:
            raise SystemExit(f"缺少必要欄位：{', '.join(missing)}")
        reserved = {"row_number", f"{args.sort_by}_rank"} & set(input_fields)
        if reserved:
            raise SystemExit(
                f"輸入檔已含輸出保留欄位：{', '.join(sorted(reserved))}"
            )
        rows = list(reader)

    selected: list[dict[str, str]] = []
    for source_row_number, row in enumerate(rows, start=2):
        if (
            not args.all_rows
            and str(row.get("direct_chinese_name", "")).strip().lower() not in TRUE_VALUES
        ):
            continue
        row["_power"] = str(number(row.get("power"), "power", source_row_number))
        row["_mystic"] = str(number(row.get("mystic"), "mystic", source_row_number))
        selected.append(row)

    primary = args.sort_by
    secondary = "mystic" if primary == "power" else "power"
    selected.sort(
        key=lambda row: (
            -float(row[f"_{primary}"]),
            -float(row[f"_{secondary}"]),
            integer(row.get("kingdom")),
            integer(row.get("local_mystic_rank")),
            row.get("player", "").casefold(),
        )
    )

    rank_field = f"{primary}_rank"
    output_fields = ["row_number", rank_field] + input_fields
    previous_value: float | None = None
    competition_rank = 0
    output_rows: list[dict[str, str | int]] = []
    for position, row in enumerate(selected, start=1):
        value = float(row[f"_{primary}"])
        if previous_value is None or value != previous_value:
            competition_rank = position
            previous_value = value
        output = {field: row.get(field, "") for field in input_fields}
        output["row_number"] = position
        output[rank_field] = competition_rank
        output_rows.append(output)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"已將 {len(output_rows)} 列依 {primary} 排序並儲存至 {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
