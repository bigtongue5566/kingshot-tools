#!/usr/bin/env python3
"""Scaffold a reproducible Kingshot event CP report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = SKILL_DIR / "assets" / "event-report-template.md"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INVALID_WINDOWS_NAME_CHARS = set('<>:"/\\|?*')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Markdown report, JSON model, and event-specific Python calculator."
    )
    parser.add_argument("--event-name", required=True, help="Traditional Chinese event name")
    parser.add_argument("--slug", required=True, help="Lowercase ASCII kebab-case event slug")
    parser.add_argument("--output-dir", required=True, type=Path, help="Artifact output directory")
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Data date in YYYY-MM-DD format (default: today)",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.event_name.strip():
        raise ValueError("--event-name cannot be empty")
    if any(char in INVALID_WINDOWS_NAME_CHARS for char in args.event_name):
        raise ValueError("--event-name contains a character that is invalid in Windows filenames")
    if not SLUG_RE.fullmatch(args.slug):
        raise ValueError("--slug must use lowercase ASCII kebab-case")
    try:
        date.fromisoformat(args.date)
    except ValueError as exc:
        raise ValueError("--date must use YYYY-MM-DD format") from exc
    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"Report template not found: {TEMPLATE_PATH}")


def calculator_template(slug: str) -> str:
    return f'''#!/usr/bin/env python3
"""Calculate the Kingshot event model in data/{slug}.json."""

from __future__ import annotations

import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "{slug}.json"


def calculate(model: dict) -> dict:
    """Replace this scaffold with the event-specific state transition and optimization."""
    raise NotImplementedError(
        "Implement the verified activity mechanics before completing the CP report."
    )


def main() -> None:
    model = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    result = calculate(model)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''


def model_template(event_name: str, slug: str, data_date: str) -> dict:
    return {
        "schemaVersion": 1,
        "event": {
            "nameZhTw": event_name,
            "nameEn": "",
            "slug": slug,
            "dataDate": data_date,
            "applicableVersion": "",
            "kingdomConditions": [],
        },
        "verification": {
            "status": "unverified",
            "serverProgressConfirmed": False,
            "packContentsConfirmed": False,
            "rewardContentsConfirmed": False,
            "mechanicsConfirmed": False,
            "confirmedBy": "",
            "confirmedAt": "",
            "serverContext": {
                "kingdomNumber": "",
                "kingdomOpenDate": "",
                "kingdomAgeDays": None,
                "heroGeneration": "",
                "truegoldStage": "",
                "progressionMarkers": [],
            },
            "evidence": [],
        },
        "sources": {
            "inGame": [],
            "eventGuides": [],
            "valuation": [],
        },
        "facts": {
            "duration": {},
            "freeResources": [],
            "purchaseRules": [],
            "resetRules": [],
        },
        "currentState": {
            "capturedAt": data_date,
            "progress": {},
            "ownedResources": [],
            "alreadyPurchasedPacks": {},
            "remainingPurchaseCaps": {},
            "activeTimers": [],
        },
        "mechanics": {
            "modelType": "",
            "state": {},
            "transitions": [],
            "probabilities": [],
            "guarantees": [],
        },
        "valuation": {
            "usdPer1000Gems": None,
            "baselineSource": "",
            "catalogStatus": "",
            "items": [],
        },
        "packs": [],
        "rewards": [],
        "milestones": [],
        "assumptions": [],
        "unresolved": [
            "Replace the scaffold with verified in-game inputs and activity mechanics."
        ],
    }


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output_dir = args.output_dir.resolve()
    report_path = output_dir / f"Kingshot-{args.event_name}-CP值報告.md"
    data_path = output_dir / "data" / f"{args.slug}.json"
    calculator_path = output_dir / "scripts" / f"calculate-{args.slug}.py"
    targets = (report_path, data_path, calculator_path)
    existing = [path for path in targets if path.exists()]
    if existing:
        print("error: refusing to overwrite existing files:", file=sys.stderr)
        for path in existing:
            print(f"  {path}", file=sys.stderr)
        return 2

    report = TEMPLATE_PATH.read_text(encoding="utf-8")
    report = (
        report.replace("{{EVENT_NAME}}", args.event_name)
        .replace("{{SLUG}}", args.slug)
        .replace("{{DATE}}", args.date)
    )

    data_path.parent.mkdir(parents=True, exist_ok=True)
    calculator_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8", newline="\n")
    data_path.write_text(
        json.dumps(
            model_template(args.event_name, args.slug, args.date),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    calculator_path.write_text(
        calculator_template(args.slug),
        encoding="utf-8",
        newline="\n",
    )

    print(report_path)
    print(data_path)
    print(calculator_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
