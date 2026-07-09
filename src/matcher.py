from __future__ import annotations

from difflib import SequenceMatcher


def fuzzy_score(query: str, value: str) -> float:
    query = (query or "").lower().strip()
    value = (value or "").lower().strip()
    if not query or not value:
        return 0.0
    try:
        from rapidfuzz import fuzz

        return float(fuzz.partial_ratio(query, value))
    except ImportError:
        return SequenceMatcher(None, query, value).ratio() * 100


def filter_prices(rows: list[dict], keyword: str | None = None, match_mode: str = "fuzzy", threshold: float = 70, **filters) -> list[dict]:
    filtered = []
    for row in rows:
        if not _passes_exact_filters(row, filters):
            continue
        if keyword:
            haystack = " ".join(
                str(row.get(field) or "")
                for field in ("product_code", "product_name", "cover_range", "size", "tier", "source_file")
            )
            if match_mode == "exact" and keyword.lower() not in haystack.lower():
                continue
            if match_mode != "exact" and fuzzy_score(keyword, haystack) < threshold:
                continue
        filtered.append(row)
    return filtered


def _passes_exact_filters(row: dict, filters: dict) -> bool:
    for field, expected in filters.items():
        if expected in (None, ""):
            continue
        if str(row.get(field) or "").upper() != str(expected).upper():
            return False
    return True
