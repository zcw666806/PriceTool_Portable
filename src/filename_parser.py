from __future__ import annotations

import re
from pathlib import Path


PDF_NAME_RE = re.compile(
    r"^(?P<supplier>[A-Z]{2,5})\s+Price\s+"
    r"(?P<body>.+?)_"
    r"(?P<version>\d{4}\.\d+)\s+"
    r"(?P<currency>[A-Z]{3})\.pdf$",
    re.IGNORECASE,
)

CODE_RE = re.compile(r"(?P<code>\d{3,6}(?:-\d{3,6})?)$")


def parse_pdf_filename(file_name: str) -> dict:
    """Parse supplier, product, version and currency from a UK Order PDF name."""
    name = Path(file_name).name
    match = PDF_NAME_RE.match(name)
    result = {
        "source_file": name,
        "supplier": None,
        "product_name": Path(name).stem,
        "product_code_raw": None,
        "product_codes": [],
        "version": None,
        "currency": None,
        "needs_review": True,
        "review_reason": "Filename does not match expected pattern",
    }
    if not match:
        return result

    body = " ".join(match.group("body").split())
    code_match = CODE_RE.search(body)
    product_code_raw = code_match.group("code") if code_match else None
    product_name = body[: code_match.start()].strip() if code_match else body
    product_codes = split_product_codes(product_code_raw)
    needs_review = not bool(product_codes)
    reason = "Product code missing in filename" if needs_review else None

    return {
        "source_file": name,
        "supplier": match.group("supplier").upper(),
        "product_name": product_name,
        "product_code_raw": product_code_raw,
        "product_codes": product_codes,
        "version": match.group("version"),
        "currency": match.group("currency").upper(),
        "needs_review": needs_review,
        "review_reason": reason,
    }


def split_product_codes(raw_code: str | None) -> list[str]:
    if not raw_code:
        return []
    raw_code = raw_code.strip()
    if "-" not in raw_code:
        return [raw_code]
    parts = [part.strip() for part in raw_code.split("-") if part.strip()]
    return parts if len(parts) > 1 else [raw_code]
