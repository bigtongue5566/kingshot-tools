#!/usr/bin/env python3
"""Validate a generated Kingshot event CP Markdown report and companion files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPORT_NAME_RE = re.compile(r"^Kingshot-.+-CP值報告(?:-.+)?\.md$", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|){2,}\s*$")
SCRIPT_SUFFIXES = {".py", ".mjs", ".js", ".ts"}

HEADING_GROUPS = {
    "資料狀態與來源": ("資料狀態與來源", "資料來源", "來源與狀態"),
    "伺服器版本與內容確認": (
        "伺服器版本與內容確認",
        "伺服器進度確認",
        "王國版本與內容確認",
    ),
    "活動玩法與模型": ("活動玩法與模型", "活動玩法", "活動規則", "活動機制"),
    "估值基準": ("估值基準", "計算基準", "Builder"),
    "禮包資料": ("禮包資料", "禮包內容", "活動禮包"),
    "免費基準": ("免費基準", "未購買基準", "免費進度"),
    "里程碑": ("里程碑",),
    "CP 結果": ("CP 結果", "禮包 CP", "CP 值", "CP值"),
    "最佳購買方案": ("最佳購買方案", "最省購買", "購買建議", "里程目標"),
    "敏感度與限制": ("敏感度與限制", "敏感度分析", "模型限制", "限制與待確認"),
    "可重算檔案": ("可重算檔案", "重算檔案", "資料檔"),
}

MODEL_REQUIRED_KEYS = {
    "schemaVersion",
    "event",
    "verification",
    "sources",
    "facts",
    "currentState",
    "mechanics",
    "valuation",
    "packs",
    "rewards",
    "milestones",
    "assumptions",
    "unresolved",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Markdown report to validate")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat unresolved placeholders and incomplete model scaffolds as errors",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    return parser.parse_args()


def extract_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if " " in target:
        target = target.split(" ", 1)[0]
    return unquote(target)


def local_links(report_path: Path, text: str) -> list[Path]:
    paths: list[Path] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = extract_target(match.group(1))
        split = urlsplit(target)
        if split.scheme or target.startswith("#"):
            continue
        relative = split.path
        if relative:
            paths.append((report_path.parent / relative).resolve())
    return paths


def has_matching_heading(headings: list[str], aliases: tuple[str, ...]) -> bool:
    return any(any(alias.casefold() in heading.casefold() for alias in aliases) for heading in headings)


def validate_model(path: Path, warnings: list[str], errors: list[str], strict: bool) -> None:
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"模型 JSON 無法讀取：{path} ({exc})")
        return
    if not isinstance(model, dict):
        errors.append(f"模型 JSON 根節點必須是物件：{path}")
        return
    missing = sorted(MODEL_REQUIRED_KEYS - set(model))
    if missing:
        errors.append(f"模型 JSON 缺少欄位：{', '.join(missing)}")
    verification = model.get("verification")
    if not isinstance(verification, dict):
        errors.append("模型 JSON 的 verification 必須是物件")
    else:
        required_flags = (
            "serverProgressConfirmed",
            "packContentsConfirmed",
            "rewardContentsConfirmed",
            "mechanicsConfirmed",
        )
        gate_passed = (
            verification.get("status") == "confirmed"
            and all(verification.get(flag) is True for flag in required_flags)
        )
        if not gate_passed:
            message = "伺服器進度、禮包、獎品與玩法確認閘門尚未全部通過"
            (errors if strict else warnings).append(message)
        server_context = verification.get("serverContext")
        if not isinstance(server_context, dict) or not any(
            value not in ("", None, [])
            for value in server_context.values()
        ):
            message = "verification.serverContext 缺少可識別的伺服器進度"
            (errors if strict else warnings).append(message)
        evidence = verification.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            message = "verification.evidence 缺少遊戲內或玩家確認證據"
            (errors if strict else warnings).append(message)
        if not verification.get("confirmedBy") or not verification.get("confirmedAt"):
            message = "verification 缺少 confirmedBy 或 confirmedAt"
            (errors if strict else warnings).append(message)
    if not isinstance(model.get("packs"), list) or not model.get("packs"):
        message = "模型缺少已確認的禮包內容"
        (errors if strict else warnings).append(message)
    current_state = model.get("currentState")
    if not isinstance(current_state, dict) or not current_state:
        message = "模型缺少目前玩家狀態 currentState"
        (errors if strict else warnings).append(message)
    else:
        state_field_groups = {
            "目前進度": (
                "progress",
                "currentVoyages",
                "currentMileage",
                "actionsCompleted",
            ),
            "現有資源": (
                "ownedResources",
                "ownedCompasses",
                "resources",
                "currency",
            ),
            "已購禮包": ("alreadyPurchasedPacks", "packsPurchased"),
        }
        missing_state_groups = [
            label
            for label, aliases in state_field_groups.items()
            if not any(alias in current_state for alias in aliases)
        ]
        if missing_state_groups:
            message = (
                "currentState 缺少邊際 CP 所需狀態："
                + ", ".join(missing_state_groups)
            )
            (errors if strict else warnings).append(message)
    rewards = model.get("rewards")
    milestones = model.get("milestones")
    if not (
        isinstance(rewards, list)
        and isinstance(milestones, list)
        and (rewards or milestones)
    ):
        message = "模型缺少已確認的獎品或里程碑內容"
        (errors if strict else warnings).append(message)
    unresolved = model.get("unresolved")
    if isinstance(unresolved, list) and unresolved:
        message = f"模型仍有 {len(unresolved)} 個 unresolved 項目"
        (errors if strict else warnings).append(message)


def validate(report_path: Path, strict: bool) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not report_path.is_file():
        return {"valid": False, "errors": [f"找不到報告：{report_path}"], "warnings": []}
    try:
        text = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {"valid": False, "errors": [f"報告不是可讀的 UTF-8：{exc}"], "warnings": []}

    if not REPORT_NAME_RE.fullmatch(report_path.name):
        errors.append("檔名必須符合 Kingshot-<活動名稱>-CP值報告.md")
    h1 = re.findall(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if len(h1) != 1 or "CP" not in h1[0].upper():
        errors.append("報告必須有且只有一個包含 CP 的 H1 標題")
    headings = re.findall(r"^##+\s+(.+)$", text, flags=re.MULTILINE)
    for label, aliases in HEADING_GROUPS.items():
        if not has_matching_heading(headings, aliases):
            errors.append(f"缺少必要章節：{label}")
    if not ISO_DATE_RE.search(text):
        errors.append("缺少 YYYY-MM-DD 資料日期")
    if "US$" not in text:
        errors.append("缺少 USD 價格或結果")
    if not ("每花 US$1" in text or re.search(r"\bCP\s*(?:定義|=)", text, re.IGNORECASE)):
        errors.append("缺少 CP 定義")
    verification_match = re.search(
        r"內容確認狀態\s*[：:]\s*(已通過|確認完成)",
        text,
    )
    if not verification_match:
        message = "報告未標示伺服器版本、禮包與獎品內容確認已通過"
        (errors if strict else warnings).append(message)
    if "邊際" not in text and "付費增量" not in text and "新增 CP" not in text:
        errors.append("缺少付費增量或邊際 CP 說明")
    if strict and not (
        "當下免費基準" in text
        or "不再加買" in text
        or "不加購" in text
    ):
        errors.append("缺少當下不再加買的免費基準")
    if strict and not ("追加禮包" in text or "新增禮包" in text):
        errors.append("主方案缺少追加禮包欄位")
    if strict and not ("追加現金" in text or "新增成本" in text):
        errors.append("主方案缺少追加現金欄位")
    if strict and "邊際 CP" not in text:
        errors.append("主方案必須明確標示邊際 CP")
    table_count = sum(
        1 for line in text.splitlines() if TABLE_SEPARATOR_RE.fullmatch(line)
    )
    if table_count < 3:
        errors.append("至少需要三個 Markdown 表格（禮包、里程碑與 CP／方案）")

    links = [extract_target(match.group(1)) for match in MARKDOWN_LINK_RE.finditer(text)]
    if not any(urlsplit(target).scheme in {"http", "https"} for target in links):
        errors.append("缺少可追溯的外部來源連結")
    resolved_links = local_links(report_path, text)
    missing_links = [path for path in resolved_links if not path.exists()]
    for path in missing_links:
        errors.append(f"本機連結不存在：{path}")

    json_paths = [path for path in resolved_links if path.suffix.casefold() == ".json"]
    script_paths = [path for path in resolved_links if path.suffix.casefold() in SCRIPT_SUFFIXES]
    if not json_paths:
        errors.append("可重算檔案必須連結至少一個 JSON 模型")
    if not script_paths:
        errors.append("可重算檔案必須連結至少一個計算腳本")
    for path in json_paths:
        if path.exists():
            validate_model(path, warnings, errors, strict)
    for path in script_paths:
        if path.exists():
            script_text = path.read_text(encoding="utf-8")
            if "NotImplementedError" in script_text:
                message = f"計算腳本仍是未實作 scaffold：{path}"
                (errors if strict else warnings).append(message)

    placeholder_count = len(re.findall(r"\[(?:待確認|待補|待計算|待完成)[^\]]*\]", text))
    if placeholder_count:
        message = f"報告仍有 {placeholder_count} 個待完成標記"
        (errors if strict else warnings).append(message)

    return {
        "valid": not errors,
        "report": str(report_path.resolve()),
        "tableCount": table_count,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    result = validate(args.report.resolve(), args.strict)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for message in result.get("errors", []):
            print(f"ERROR: {message}")
        for message in result.get("warnings", []):
            print(f"WARNING: {message}")
        if result["valid"]:
            print(f"OK: {result['report']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
