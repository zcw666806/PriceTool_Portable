from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_size_mapping() -> dict[str, str]:
    path = ROOT / "config" / "size_mapping.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_space(value) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def normalize_key(value) -> str:
    value = normalize_space(value).upper()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s*/\s*", "/", value)
    return value


def normalize_size(raw_size) -> dict:
    raw = normalize_space(raw_size)
    key = normalize_key(raw)
    mapping = load_size_mapping()
    if key in mapping:
        return {
            "size": mapping[key],
            "size_raw": raw,
            "confidence": 1.0,
            "needs_review": False,
            "review_reason": None,
        }

    compact = key.replace(" ", "")
    if re.fullmatch(r"\d(?:\.5)?S(?:\+\w+)?", compact) or re.fullmatch(r"\d-C-\d", compact):
        return {
            "size": compact,
            "size_raw": raw,
            "confidence": 0.95,
            "needs_review": False,
            "review_reason": None,
        }

    simplified = key.replace("-", " ")
    if simplified in mapping:
        return {
            "size": mapping[simplified],
            "size_raw": raw,
            "confidence": 0.95,
            "needs_review": False,
            "review_reason": None,
        }

    return {
        "size": raw.upper() if raw else None,
        "size_raw": raw,
        "confidence": 0.3 if raw else 0.0,
        "needs_review": True,
        "review_reason": "Size could not be mapped",
    }


def is_probable_size(value) -> bool:
    normalized = normalize_size(value)
    if not normalized["needs_review"]:
        return True
    key = normalize_key(value)
    tokens = (
        "SEATER",
        "SOFA",
        "CHAIR",
        "FOOT",
        "STOOL",
        "OTTOMAN",
        "CORNER",
        "CHAISE",
        "WING",
        "ARM",
    )
    return any(token in key for token in tokens)


def build_lookup_key(*parts) -> str:
    return "|".join(normalize_key(part) for part in parts if normalize_space(part))
