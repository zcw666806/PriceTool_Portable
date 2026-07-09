from __future__ import annotations

import re


EMPTY_VALUES = {"", "-", "N/A", "NA", "NONE", "NULL"}


def clean_price(raw_value, min_price: float = 100, max_price: float = 5000) -> dict:
    raw_text = "" if raw_value is None else str(raw_value).strip()
    if raw_text.upper() in EMPTY_VALUES:
        return {
            "price": None,
            "raw_price": raw_text,
            "needs_review": True,
            "review_reason": "Price is blank",
        }

    compact = raw_text.replace("\n", " ")
    compact = re.sub(r"[$£€]", "", compact)
    compact = re.sub(r"\s*,\s*", ",", compact)
    compact = re.sub(r"(?<=\d)\s+(?=\d)", "", compact)
    compact = compact.replace(",", "")
    compact = compact.strip()

    if not re.fullmatch(r"\d+(?:\.\d+)?", compact):
        return {
            "price": None,
            "raw_price": raw_text,
            "needs_review": True,
            "review_reason": "Price could not be converted",
        }

    price = float(compact)
    needs_review = price < min_price or price > max_price
    reason = "Price outside expected range" if needs_review else None
    return {
        "price": price,
        "raw_price": raw_text,
        "needs_review": needs_review,
        "review_reason": reason,
    }


def price_to_number(raw_value):
    return clean_price(raw_value)["price"]
