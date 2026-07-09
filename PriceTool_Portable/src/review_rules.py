from __future__ import annotations

from collections import defaultdict


def mark_version_conflicts(rows: list[dict]) -> list[dict]:
    versions_by_product = defaultdict(set)
    for row in rows:
        if row.get("product_code") and row.get("version"):
            versions_by_product[row["product_code"]].add(row["version"])

    conflict_products = {code for code, versions in versions_by_product.items() if len(versions) > 1}
    for row in rows:
        if row.get("product_code") in conflict_products:
            reason = row.get("review_reason") or ""
            addition = "Multiple versions exist for product"
            if addition not in reason:
                row["review_reason"] = "; ".join(part for part in [reason, addition] if part)
            row["needs_review"] = True
    return rows


def mark_duplicate_price_conflicts(rows: list[dict]) -> list[dict]:
    by_key = defaultdict(set)
    for row in rows:
        key = (
            row.get("product_code"),
            row.get("tier"),
            row.get("cover_range"),
            row.get("cover_type"),
            row.get("size"),
            row.get("source_type"),
        )
        if row.get("price") is not None:
            by_key[key].add(row.get("price"))

    conflict_keys = {key for key, prices in by_key.items() if len(prices) > 1}
    for row in rows:
        key = (
            row.get("product_code"),
            row.get("tier"),
            row.get("cover_range"),
            row.get("cover_type"),
            row.get("size"),
            row.get("source_type"),
        )
        if key in conflict_keys:
            reason = row.get("review_reason") or ""
            addition = "Same lookup key has different prices"
            if addition not in reason:
                row["review_reason"] = "; ".join(part for part in [reason, addition] if part)
            row["needs_review"] = True
    return rows
