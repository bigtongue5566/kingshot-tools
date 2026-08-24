from __future__ import annotations

import json
import os
import tempfile
import unicodedata
from copy import deepcopy
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_BASE_GLOSSARY = Path(__file__).resolve().parent.parent / "references" / "terms.base.json"
DATA_DIR_ENV = "KINGSHOT_DATA_DIR"


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = normalize(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def names(term: dict[str, Any], language: str) -> list[str]:
    if language == "zh":
        return [term["zhTw"], *term.get("aliasesZhTw", [])]
    return [term["en"], *term.get("aliasesEn", [])]


def default_user_glossary() -> Path:
    configured = os.environ.get(DATA_DIR_ENV)
    data_root = Path(configured).expanduser() if configured else Path.home() / ".kingshot"
    return data_root / "glossary" / "terms.user.json"


def empty_user_glossary() -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "updatedAt": None,
        "notes": [
            "User-confirmed Kingshot translation pairs. This file is preserved separately from skill updates."
        ],
        "sources": {},
        "terms": [],
    }


def read_glossary(path: Path, *, missing_ok: bool = False) -> dict[str, Any]:
    if missing_ok and not path.exists():
        return empty_user_glossary()
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Glossary root must be an object: {path}")
    return data


def validate_glossary(
    glossary: dict[str, Any],
    *,
    label: str,
    known_source_ids: set[str] | None = None,
) -> None:
    if glossary.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"{label} must use schemaVersion {SCHEMA_VERSION!r}.")
    if not isinstance(glossary.get("terms"), list) or not isinstance(glossary.get("sources"), dict):
        raise ValueError(f"{label} must contain a terms list and sources object.")

    for source_id, metadata in glossary["sources"].items():
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"{label} contains an empty source ID.")
        if not isinstance(metadata, dict) or not isinstance(metadata.get("type"), str):
            raise ValueError(f"{label} source {source_id!r} must be an object with a string type.")

    available_sources = known_source_ids if known_source_ids is not None else set(glossary["sources"])
    owners: dict[tuple[str, str], tuple[str, str]] = {}
    pairs: set[tuple[str, str]] = set()
    for term in glossary["terms"]:
        if not isinstance(term, dict):
            raise ValueError(f"{label} terms must be objects.")
        for field in ("zhTw", "en", "category", "status"):
            if not isinstance(term.get(field), str) or not term[field].strip():
                raise ValueError(f"{label} term field {field!r} must be a non-empty string.")
        if term["status"] != "confirmed":
            raise ValueError(f"Only confirmed terms may be stored: {term['zhTw']} / {term['en']}")
        for field in ("aliasesZhTw", "aliasesEn", "sourceIds"):
            if not isinstance(term.get(field, []), list) or not all(
                isinstance(value, str) and value.strip() for value in term.get(field, [])
            ):
                raise ValueError(f"{label} term field {field!r} must be a list of non-empty strings.")

        pair = (normalize(term["zhTw"]), normalize(term["en"]))
        if pair in pairs:
            raise ValueError(f"Duplicate pair in {label}: {term['zhTw']} / {term['en']}")
        pairs.add(pair)

        display_pair = (term["zhTw"], term["en"])
        for language in ("zh", "en"):
            for name in names(term, language):
                key = (language, normalize(name))
                if not key[1]:
                    raise ValueError(f"Empty normalized name in pair: {display_pair[0]} / {display_pair[1]}")
                previous = owners.get(key)
                if previous is not None and previous != display_pair:
                    raise ValueError(
                        f"Name collision for {name!r}: {previous[0]} / {previous[1]} "
                        f"versus {display_pair[0]} / {display_pair[1]}"
                    )
                owners[key] = display_pair

        missing_sources = [
            source_id for source_id in term.get("sourceIds", []) if source_id not in available_sources
        ]
        if missing_sources:
            raise ValueError(
                f"Unknown source IDs for {display_pair[0]} / {display_pair[1]}: "
                + ", ".join(missing_sources)
            )


def locate_pair(terms: list[dict[str, Any]], zh_tw: str, en: str) -> dict[str, Any] | None:
    zh_key = normalize(zh_tw)
    en_key = normalize(en)
    exact_pair: dict[str, Any] | None = None

    for term in terms:
        same_zh = any(normalize(name) == zh_key for name in names(term, "zh"))
        same_en = any(normalize(name) == en_key for name in names(term, "en"))
        if same_zh and same_en:
            exact_pair = term
            continue
        if same_zh:
            raise ValueError(
                f"Conflict: {zh_tw!r} already maps to {term['en']!r}, not {en!r}. "
                "Ask the user before changing it."
            )
        if same_en:
            raise ValueError(
                f"Conflict: {en!r} already maps to {term['zhTw']!r}, not {zh_tw!r}. "
                "Ask the user before changing it."
            )

    return exact_pair


def assert_aliases_available(
    terms: list[dict[str, Any]],
    current: dict[str, Any] | None,
    aliases: list[str],
    language: str,
) -> None:
    for alias in aliases:
        alias_key = normalize(alias)
        for term in terms:
            if term is current:
                continue
            if any(normalize(name) == alias_key for name in names(term, language)):
                raise ValueError(
                    f"Alias conflict: {alias!r} already belongs to {term['zhTw']!r} / {term['en']!r}."
                )


def _merge_sources(base_sources: dict[str, Any], user_sources: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base_sources)
    for source_id, overlay in user_sources.items():
        if source_id not in merged:
            merged[source_id] = deepcopy(overlay)
            continue
        for field, value in overlay.items():
            if field in merged[source_id] and merged[source_id][field] != value:
                raise ValueError(
                    f"Source conflict for {source_id!r} field {field!r}. Ask the user before replacing it."
                )
            merged[source_id][field] = deepcopy(value)
    return merged


def _merge_term(current: dict[str, Any], overlay: dict[str, Any]) -> None:
    if current["category"] != overlay["category"]:
        raise ValueError(
            f"Category conflict for {current['zhTw']} / {current['en']}: "
            f"{current['category']!r} versus {overlay['category']!r}."
        )
    if overlay.get("notes") and current.get("notes") not in (None, overlay["notes"]):
        raise ValueError(
            f"Notes conflict for {current['zhTw']} / {current['en']}. Ask the user before replacing it."
        )

    current["aliasesZhTw"] = unique([*current.get("aliasesZhTw", []), *overlay.get("aliasesZhTw", [])])
    current["aliasesEn"] = unique([*current.get("aliasesEn", []), *overlay.get("aliasesEn", [])])
    current["sourceIds"] = unique([*current.get("sourceIds", []), *overlay.get("sourceIds", [])])
    if overlay.get("verifiedAt"):
        current["verifiedAt"] = overlay["verifiedAt"]
    if overlay.get("notes") and "notes" not in current:
        current["notes"] = overlay["notes"]


def merge_glossaries(base: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    validate_glossary(base, label="base glossary")
    merged_sources = _merge_sources(base["sources"], user.get("sources", {}))
    validate_glossary(user, label="user glossary", known_source_ids=set(merged_sources))

    merged_terms = deepcopy(base["terms"])
    for overlay in user["terms"]:
        current = locate_pair(merged_terms, overlay["zhTw"], overlay["en"])
        assert_aliases_available(merged_terms, current, overlay.get("aliasesZhTw", []), "zh")
        assert_aliases_available(merged_terms, current, overlay.get("aliasesEn", []), "en")
        if current is None:
            merged_terms.append(deepcopy(overlay))
        else:
            _merge_term(current, overlay)

    merged = {
        "schemaVersion": SCHEMA_VERSION,
        "updatedAt": user.get("updatedAt") or base.get("updatedAt"),
        "notes": list(dict.fromkeys([*base.get("notes", []), *user.get("notes", [])])),
        "sources": merged_sources,
        "terms": merged_terms,
    }
    validate_glossary(merged, label="merged glossary")
    return merged


def load_layers(base_path: Path, user_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    base = read_glossary(base_path)
    user = read_glossary(user_path, missing_ok=True)
    return base, user, merge_glossaries(base, user)


def write_atomic(path: Path, glossary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(glossary, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temporary_path = Path(handle.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
