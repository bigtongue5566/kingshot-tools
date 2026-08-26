#!/usr/bin/env python3
"""以遊戲內 Governor ID 建立或更新 Kingshot 玩家名冊。"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


FIELDS = [
    "governor_id",
    "tracker_uid",
    "current_kingdom",
    "current_name",
    "known_names",
    "provided_label",
    "rank_hint",
    "match_status",
    "id_source",
    "id_last_checked",
    "notes",
]


def positive_digits(value: str, label: str, *, allow_blank: bool = False) -> str:
    text = value.strip()
    if allow_blank and not text:
        return ""
    if not text.isdecimal() or int(text) < 1:
        raise argparse.ArgumentTypeError(f"{label} 必須是正十進位整數")
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry_csv", type=Path)
    parser.add_argument("--governor-id", required=True)
    parser.add_argument("--tracker-uid", default="")
    parser.add_argument("--kingdom", required=True)
    parser.add_argument("--current-name", required=True)
    parser.add_argument("--provided-label", default="")
    parser.add_argument("--rank-hint", default="")
    parser.add_argument("--match-status", required=True)
    parser.add_argument("--id-source", required=True)
    parser.add_argument("--checked-at", required=True)
    parser.add_argument("--notes", default="")
    return parser.parse_args()


def read_registry(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        if fields != FIELDS:
            raise SystemExit(
                "名冊欄位不符合預期結構：" + ",".join(FIELDS)
            )
        return list(reader)


def aliases(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def main() -> int:
    args = parse_args()
    governor_id = positive_digits(args.governor_id, "governor_id")
    tracker_uid = positive_digits(args.tracker_uid, "tracker_uid", allow_blank=True)
    kingdom = positive_digits(args.kingdom.removeprefix("K").removeprefix("k"), "kingdom")
    rank_hint = positive_digits(args.rank_hint, "rank_hint", allow_blank=True)
    current_name = args.current_name.strip()
    if not current_name:
        raise SystemExit("current_name 不可為空")

    rows = read_registry(args.registry_csv)
    matching = [row for row in rows if row["governor_id"].strip() == governor_id]
    if len(matching) > 1:
        raise SystemExit(f"名冊已有重複 governor_id：{governor_id}")

    if matching:
        row = matching[0]
        tracker_uid = tracker_uid or row.get("tracker_uid", "").strip()
        rank_hint = rank_hint or row.get("rank_hint", "").strip()
        history = aliases(row.get("known_names", ""))
        former_name = row.get("current_name", "").strip()
        if former_name and former_name != current_name and former_name not in history:
            history.append(former_name)
    else:
        row = {field: "" for field in FIELDS}
        rows.append(row)
        history = []

    provided_label = args.provided_label.strip() or row.get("provided_label", "").strip()
    notes = args.notes.strip() or row.get("notes", "").strip()
    if provided_label and provided_label != current_name and provided_label not in history:
        history.append(provided_label)

    row.update(
        {
            "governor_id": governor_id,
            "tracker_uid": tracker_uid,
            "current_kingdom": kingdom,
            "current_name": current_name,
            "known_names": " | ".join(history),
            "provided_label": provided_label,
            "rank_hint": rank_hint,
            "match_status": args.match_status.strip(),
            "id_source": args.id_source.strip(),
            "id_last_checked": args.checked_at.strip(),
            "notes": notes,
        }
    )

    rows.sort(key=lambda item: (int(item["current_kingdom"]), item["current_name"].casefold()))
    args.registry_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.registry_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"已儲存 {len(rows)} 筆名冊；更新 governor_id {governor_id}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
