from __future__ import annotations

import re
from pathlib import Path

from .filename_parser import parse_pdf_filename
from .normalizer import build_lookup_key, is_probable_size, normalize_key, normalize_size, normalize_space
from .price_cleaner import clean_price


META_ALIASES = {
    "section": {"SECTION", "FABRIC/LEATHER", "FABRIC", "LEATHER"},
    "tier": {"TIER", "GRADE", "PRICE TIER"},
    "cover_range": {"COVER RANGE", "COVER", "RANGE", "FABRIC RANGE", "LEATHER RANGE"},
    "cover_type": {"TYPE", "COVER TYPE", "FABRIC TYPE", "LEATHER TYPE"},
}


def scan_pdf_folder(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"PDF folder not found: {folder}")
    return sorted(path for path in folder.glob("*.pdf") if path.is_file())


def extract_pdf_tables(pdf_path: str | Path) -> list[dict]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("Missing dependency: pdfplumber") from exc

    pdf_path = Path(pdf_path)
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            extracted = page.extract_tables() or []
            for table_index, rows in enumerate(extracted):
                tables.append(
                    {
                        "source_file": pdf_path.name,
                        "source_path": str(pdf_path),
                        "page": page_index,
                        "table_index": table_index,
                        "rows": rows,
                    }
                )
    return tables


def flatten_pdf_raw(tables: list[dict]) -> list[dict]:
    raw_rows = []
    for table in tables:
        for row_index, row in enumerate(table.get("rows") or []):
            for column_index, value in enumerate(row or []):
                raw_rows.append(
                    {
                        "source_file": table.get("source_file"),
                        "page": table.get("page"),
                        "table_index": table.get("table_index"),
                        "row_index": row_index,
                        "column_index": column_index,
                        "raw_text": "" if value is None else str(value),
                    }
                )
    return raw_rows


def tables_to_price_rows(tables: list[dict], import_batch_id: str | None = None) -> list[dict]:
    price_rows = []
    for table in tables:
        parsed = parse_pdf_filename(table["source_file"])
        rows = _clean_table_rows(table.get("rows") or [])
        header_index = _find_header_row(rows)
        if header_index is None:
            continue
        header = rows[header_index]
        meta_columns, size_columns = _classify_columns(header, rows[header_index + 1 :])
        carry = {"section": None, "tier": None, "cover_range": None, "cover_type": None}
        for row_index, row in enumerate(rows[header_index + 1 :], start=header_index + 1):
            if not any(normalize_space(cell) for cell in row):
                continue
            if any("NO. CUSHIONS" in normalize_key(cell) for cell in row):
                continue
            _update_section_from_separator(carry, row, size_columns)
            _update_carry(carry, meta_columns, row)
            for col_idx, raw_size in size_columns.items():
                raw_price = row[col_idx] if col_idx < len(row) else None
                cleaned = clean_price(raw_price)
                if cleaned["price"] is None and not normalize_space(raw_price):
                    continue
                size = normalize_size(raw_size)
                review_reasons = [
                    reason
                    for reason in (
                        parsed.get("review_reason"),
                        size.get("review_reason") if size.get("needs_review") else None,
                        cleaned.get("review_reason") if cleaned.get("needs_review") else None,
                    )
                    if reason
                ]
                product_codes = parsed.get("product_codes") or [None]
                for product_code in product_codes:
                    price_rows.append(
                        {
                            "source_file": table.get("source_file"),
                            "source_path": table.get("source_path"),
                            "source_type": "PDF",
                            "source_role": "PRIMARY",
                            "source_profile": "PDF_PRICE_LIST",
                            "import_batch_id": import_batch_id,
                            "supplier": parsed.get("supplier"),
                            "price_basis": "FOB",
                            "currency": parsed.get("currency"),
                            "version": parsed.get("version"),
                            "effective_date": None,
                            "product_code": product_code,
                            "product_name": parsed.get("product_name"),
                            "collection": None,
                            "section": carry.get("section"),
                            "tier": carry.get("tier"),
                            "cover_range": carry.get("cover_range"),
                            "cover_type": carry.get("cover_type"),
                            "size": size.get("size"),
                            "size_raw": size.get("size_raw"),
                            "price": cleaned.get("price"),
                            "raw_price": cleaned.get("raw_price"),
                            "formula": None,
                            "page": table.get("page"),
                            "table_index": table.get("table_index"),
                            "row_index": row_index,
                            "confidence": _confidence(parsed, size, cleaned),
                            "needs_review": bool(review_reasons),
                            "review_reason": "; ".join(dict.fromkeys(review_reasons)),
                            "lookup_key": build_lookup_key(
                                product_code,
                                parsed.get("product_name"),
                                carry.get("tier"),
                                carry.get("cover_range"),
                                size.get("size"),
                            ),
                        }
                    )
    return price_rows


def extract_pdf_file(pdf_path: str | Path, import_batch_id: str | None = None) -> dict:
    tables = extract_pdf_tables(pdf_path)
    return {
        "tables": tables,
        "raw_rows": flatten_pdf_raw(tables),
        "price_rows": tables_to_price_rows(tables, import_batch_id=import_batch_id),
    }


def _clean_table_rows(rows: list[list]) -> list[list[str]]:
    width = max((len(row or []) for row in rows), default=0)
    cleaned = []
    for row in rows:
        row = row or []
        cleaned.append([normalize_space(row[idx] if idx < len(row) else "") for idx in range(width)])
    return cleaned


def _find_header_row(rows: list[list[str]]) -> int | None:
    start_index = 0
    has_currency_marker = False
    for index, row in enumerate(rows[:10]):
        row_text = " ".join(normalize_space(cell) for cell in row)
        if any(marker in row_text.upper() for marker in ("FOB", "CIF", "US$", "GBP", "USD")):
            start_index = index + 1
            has_currency_marker = True
            break
    if not has_currency_marker:
        return None
    for index, row in enumerate(rows[start_index : start_index + 8], start=start_index):
        row_text = " ".join(normalize_space(cell) for cell in row)
        if len(row_text) > 220:
            continue
        size_count = len(_extract_size_tokens(row))
        if size_count >= 2:
            return index
    return None


def _classify_columns(header: list[str], body_rows: list[list[str]]) -> tuple[dict[str, int], dict[int, str]]:
    meta_columns = {}
    size_columns = {}
    for col_idx, value in enumerate(header):
        key = normalize_key(value)
        if not key:
            continue
        assigned = False
        for field, aliases in META_ALIASES.items():
            if key in aliases and field not in meta_columns:
                meta_columns[field] = col_idx
                assigned = True
                break
        if not assigned and len(value) <= 40 and len(_extract_size_tokens([value])) <= 2 and is_probable_size(value):
            size_columns[col_idx] = value
    if "cover_range" not in meta_columns:
        for idx, value in enumerate(header[:4]):
            if normalize_key(value) in {"COVER", "RANGE", "COVER RANGE"}:
                meta_columns["cover_range"] = idx
    if not size_columns:
        tokens = _extract_size_tokens(header)
        price_columns = _infer_price_columns(body_rows)
        if tokens and price_columns:
            for col_idx, token in zip(price_columns, tokens):
                size_columns[col_idx] = token
            first_price_col = min(size_columns)
            if first_price_col >= 4:
                meta_columns.setdefault("cover_type", first_price_col - 1)
                meta_columns.setdefault("cover_range", first_price_col - 2)
                meta_columns.setdefault("tier", 1)
            elif first_price_col >= 3:
                meta_columns.setdefault("cover_range", first_price_col - 1)
                meta_columns.setdefault("tier", 1)
    return meta_columns, size_columns


def _update_carry(carry: dict, meta_columns: dict[str, int], row: list[str]) -> None:
    for field, col_idx in meta_columns.items():
        value = row[col_idx] if col_idx < len(row) else ""
        value = normalize_space(value)
        if value:
            carry[field] = value
    first_data = normalize_space(row[1] if len(row) > 1 else "")
    if first_data and not _looks_like_tier(first_data) and "No. Cushions" not in first_data:
        if not normalize_space(row[2] if len(row) > 2 else ""):
            carry["cover_range"] = first_data
        elif first_data.upper() in {"FIXED", "POWER", "MANUAL", "SCATTER BACK", "FORMAL BACK", "FABRIC", "LEATHER"}:
            carry["section"] = first_data


def _confidence(parsed: dict, size: dict, cleaned: dict) -> float:
    score = 1.0
    if parsed.get("needs_review"):
        score -= 0.25
    if size.get("needs_review"):
        score -= 0.25
    if cleaned.get("needs_review"):
        score -= 0.25
    return max(score, 0.1)


def _extract_size_tokens(row: list[str]) -> list[str]:
    text = " ".join(normalize_space(cell) for cell in row if normalize_space(cell))
    text = text.replace("\n", " ")
    raw_tokens = re.findall(
        r"\b(?:\d(?:\.5)?\s*-?\s*SEATER|\d(?:\.5)?S(?:\+\w+)?|\d-C-\d|[1-4]|FOOTSTOOL|OTTOMAN|CORNER|CHAISE|ARMCHAIR|AC|CHAIR)\b",
        text,
        flags=re.IGNORECASE,
    )
    tokens = []
    for token in raw_tokens:
        cleaned = normalize_space(token).upper().replace(" ", "")
        if cleaned in {"1", "2", "3", "4"}:
            cleaned = f"{cleaned}S"
        if cleaned == "AC":
            cleaned = "ARMCHAIR"
        if cleaned.endswith("SEATER"):
            cleaned = cleaned.replace("SEATER", "S").replace("-", "")
        if cleaned not in tokens:
            tokens.append(cleaned)
    return tokens


def _infer_price_columns(body_rows: list[list[str]]) -> list[int]:
    scores: dict[int, int] = {}
    for row in body_rows[:20]:
        for col_idx, value in enumerate(row):
            text = normalize_space(value)
            if not text:
                continue
            cleaned = clean_price(text)
            if cleaned["price"] is not None or text == "-":
                scores[col_idx] = scores.get(col_idx, 0) + 1
    return [col for col, _ in sorted(scores.items(), key=lambda item: item[0]) if col > 1]


def _update_section_from_separator(carry: dict, row: list[str], size_columns: dict[int, str]) -> None:
    if any(normalize_space(row[col]) for col in size_columns if col < len(row)):
        return
    non_empty = [(idx, normalize_space(value)) for idx, value in enumerate(row) if normalize_space(value)]
    if len(non_empty) == 1:
        _, value = non_empty[0]
        upper = value.upper()
        if upper in {"FABRIC", "LEATHER", "SCATTER BACK", "FORMAL BACK", "FIXED", "POWER", "MANUAL"}:
            carry["section"] = value


def _looks_like_tier(value: str) -> bool:
    value = normalize_space(value).upper()
    return bool(re.fullmatch(r"[A-Z]", value) or re.fullmatch(r"[A-Z]/[A-Z]", value))
