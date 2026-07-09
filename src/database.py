from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import PRICE_COLUMNS


SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    source_path TEXT,
    source_type TEXT,
    source_role TEXT,
    source_profile TEXT,
    import_batch_id TEXT,
    supplier TEXT,
    price_basis TEXT,
    currency TEXT,
    version TEXT,
    effective_date TEXT,
    product_code TEXT,
    product_name TEXT,
    collection TEXT,
    section TEXT,
    tier TEXT,
    cover_range TEXT,
    cover_type TEXT,
    size TEXT,
    size_raw TEXT,
    price REAL,
    raw_price TEXT,
    formula TEXT,
    page INTEGER,
    table_index INTEGER,
    row_index INTEGER,
    confidence REAL,
    needs_review INTEGER DEFAULT 0,
    review_reason TEXT,
    lookup_key TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT,
    product_name TEXT,
    supplier TEXT,
    alias_name TEXT,
    source_file TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS colour_reference (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colour_code TEXT,
    colour_name TEXT,
    category TEXT,
    cover_range TEXT,
    price_tier TEXT,
    cover_type TEXT,
    notes TEXT,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS source_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    file_path TEXT,
    file_type TEXT,
    source_role TEXT,
    source_profile TEXT,
    optional_source INTEGER DEFAULT 0,
    file_hash TEXT,
    imported_at TEXT,
    status TEXT,
    page_count INTEGER,
    table_count INTEGER,
    row_count INTEGER,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS pdf_extract_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    page INTEGER,
    table_index INTEGER,
    row_index INTEGER,
    column_index INTEGER,
    raw_text TEXT
);

CREATE TABLE IF NOT EXISTS excel_imported_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    sheet_name TEXT,
    row_number INTEGER,
    column_number INTEGER,
    value TEXT,
    formula TEXT
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def clear_imported_data(conn: sqlite3.Connection) -> None:
    for table in (
        "prices",
        "products",
        "colour_reference",
        "source_files",
        "pdf_extract_raw",
        "excel_imported_raw",
    ):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def insert_prices(conn: sqlite3.Connection, rows: Iterable[dict]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    now = datetime.now().isoformat(timespec="seconds")
    cols = PRICE_COLUMNS + ["created_at", "updated_at"]
    values = []
    for row in rows:
        item = {col: row.get(col) for col in PRICE_COLUMNS}
        item["needs_review"] = int(bool(item.get("needs_review")))
        item["created_at"] = now
        item["updated_at"] = now
        values.append([item.get(col) for col in cols])
    placeholders = ",".join("?" for _ in cols)
    conn.executemany(
        f"INSERT INTO prices ({','.join(cols)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return len(rows)


def insert_source_file(conn: sqlite3.Connection, row: dict) -> None:
    cols = [
        "file_name",
        "file_path",
        "file_type",
        "source_role",
        "source_profile",
        "optional_source",
        "file_hash",
        "imported_at",
        "status",
        "page_count",
        "table_count",
        "row_count",
        "error_message",
    ]
    item = {col: row.get(col) for col in cols}
    item["optional_source"] = int(bool(item.get("optional_source")))
    item["imported_at"] = item.get("imported_at") or datetime.now().isoformat(timespec="seconds")
    conn.execute(
        f"INSERT INTO source_files ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [item.get(col) for col in cols],
    )
    conn.commit()


def insert_pdf_raw(conn: sqlite3.Connection, rows: Iterable[dict]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    cols = ["source_file", "page", "table_index", "row_index", "column_index", "raw_text"]
    conn.executemany(
        f"INSERT INTO pdf_extract_raw ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [[row.get(col) for col in cols] for row in rows],
    )
    conn.commit()
    return len(rows)


def insert_excel_raw(conn: sqlite3.Connection, rows: Iterable[dict]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    cols = ["source_file", "sheet_name", "row_number", "column_number", "value", "formula"]
    conn.executemany(
        f"INSERT INTO excel_imported_raw ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [[row.get(col) for col in cols] for row in rows],
    )
    conn.commit()
    return len(rows)


def insert_products(conn: sqlite3.Connection, rows: Iterable[dict]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    cols = ["product_code", "product_name", "supplier", "alias_name", "source_file", "active"]
    values = []
    seen = set()
    for row in rows:
        key = (row.get("product_code"), row.get("product_name"), row.get("source_file"))
        if key in seen:
            continue
        seen.add(key)
        values.append([row.get(col, 1 if col == "active" else None) for col in cols])
    conn.executemany(
        f"INSERT INTO products ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        values,
    )
    conn.commit()
    return len(values)


def insert_colour_reference(conn: sqlite3.Connection, rows: Iterable[dict]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    cols = [
        "colour_code",
        "colour_name",
        "category",
        "cover_range",
        "price_tier",
        "cover_type",
        "notes",
        "source_file",
    ]
    conn.executemany(
        f"INSERT INTO colour_reference ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [[row.get(col) for col in cols] for row in rows],
    )
    conn.commit()
    return len(rows)


def build_price_where(filters: dict | None = None) -> tuple[str, list]:
    filters = filters or {}
    where = []
    params = []

    exact_fields = [
        "product_code",
        "product_name",
        "supplier",
        "version",
        "currency",
        "section",
        "tier",
        "cover_range",
        "size",
        "price_basis",
    ]
    for field in exact_fields:
        value = filters.get(field)
        if value:
            where.append(f"UPPER(COALESCE({field}, '')) = UPPER(?)")
            params.append(str(value))

    keyword = filters.get("keyword")
    if keyword:
        like = f"%{keyword}%"
        where.append(
            "(product_code LIKE ? OR product_name LIKE ? OR cover_range LIKE ? OR size LIKE ? OR source_file LIKE ?)"
        )
        params.extend([like] * 5)

    source_file = filters.get("source_file")
    if source_file:
        where.append("source_file LIKE ?")
        params.append(f"%{source_file}%")

    if filters.get("needs_review") is not None:
        where.append("needs_review = ?")
        params.append(1 if filters.get("needs_review") else 0)

    if filters.get("min_price") not in (None, ""):
        where.append("price >= ?")
        params.append(float(filters["min_price"]))
    if filters.get("max_price") not in (None, ""):
        where.append("price <= ?")
        params.append(float(filters["max_price"]))

    return (" WHERE " + " AND ".join(where)) if where else "", params


def query_prices(conn: sqlite3.Connection, filters: dict | None = None, limit: int | None = 500, offset: int = 0) -> list[dict]:
    where_sql, params = build_price_where(filters)
    sql = "SELECT * FROM prices"
    sql += where_sql
    sql += " ORDER BY product_code, product_name, tier, cover_range, size"
    if limit:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    return [dict(row) for row in conn.execute(sql, params)]


def query_table(conn: sqlite3.Connection, table: str, limit: int | None = 500) -> list[dict]:
    allowed = {"prices", "products", "colour_reference", "source_files", "pdf_extract_raw", "excel_imported_raw"}
    if table not in allowed:
        raise ValueError(f"Unsupported table: {table}")
    sql = f"SELECT * FROM {table}"
    if limit:
        sql += " LIMIT ?"
        return [dict(row) for row in conn.execute(sql, [limit])]
    return [dict(row) for row in conn.execute(sql)]


def count_prices(conn: sqlite3.Connection, filters: dict | None = None) -> int:
    where_sql, params = build_price_where(filters)
    sql = "SELECT COUNT(*) FROM prices" + where_sql
    return int(conn.execute(sql, params).fetchone()[0])


def get_summary(conn: sqlite3.Connection) -> dict:
    price_count = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
    review_count = conn.execute("SELECT COUNT(*) FROM prices WHERE needs_review = 1").fetchone()[0]
    source_count = conn.execute("SELECT COUNT(*) FROM source_files").fetchone()[0]
    product_count = conn.execute("SELECT COUNT(DISTINCT COALESCE(product_code, product_name)) FROM prices").fetchone()[0]
    return {
        "price_count": price_count,
        "review_count": review_count,
        "source_count": source_count,
        "product_count": product_count,
    }
