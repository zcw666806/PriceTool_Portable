from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .cache_manager import file_hash
from .database import (
    clear_imported_data,
    connect,
    get_summary,
    init_db,
    insert_colour_reference,
    insert_excel_raw,
    insert_pdf_raw,
    insert_prices,
    insert_products,
    insert_source_file,
    query_prices,
    query_table,
)
from .excel_reader import import_excel_workbook
from .exporter import export_workbook
from .filename_parser import parse_pdf_filename
from .pdf_table_extractor import extract_pdf_file, scan_pdf_folder
from .review_rules import mark_duplicate_price_conflicts, mark_version_conflicts


ROOT = Path(__file__).resolve().parents[1]


def load_config() -> dict:
    path = ROOT / "config" / "app_config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def open_database(db_path: str | Path | None = None):
    config = load_config()
    db_path = resolve_project_path(db_path or config["database_path"])
    conn = connect(db_path)
    init_db(conn)
    return conn


def preview_pdf_folder(folder: str | Path) -> list[dict]:
    files = scan_pdf_folder(folder)
    rows = []
    for path in files:
        parsed = parse_pdf_filename(path.name)
        rows.append(
            {
                "file_name": path.name,
                "supplier": parsed.get("supplier"),
                "product_name": parsed.get("product_name"),
                "product_codes": ", ".join(parsed.get("product_codes") or []),
                "version": parsed.get("version"),
                "currency": parsed.get("currency"),
                "needs_review": parsed.get("needs_review"),
                "review_reason": parsed.get("review_reason"),
            }
        )
    return rows


def start_import(
    pdf_folder: str | Path,
    excel_files: list[str | Path] | None = None,
    db_path: str | Path | None = None,
    clear_existing: bool = True,
    progress_callback=None,
) -> dict:
    conn = open_database(db_path)
    if clear_existing:
        clear_imported_data(conn)

    batch_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid4().hex[:8]
    all_price_rows = []
    all_products = []
    stats = {
        "batch_id": batch_id,
        "pdf_files": 0,
        "excel_files": 0,
        "price_rows": 0,
        "raw_pdf_rows": 0,
        "raw_excel_rows": 0,
        "errors": [],
    }

    pdf_paths = scan_pdf_folder(pdf_folder)
    for index, pdf_path in enumerate(pdf_paths, start=1):
        if progress_callback:
            progress_callback(index, len(pdf_paths), pdf_path.name)
        try:
            extracted = extract_pdf_file(pdf_path, import_batch_id=batch_id)
            parsed = parse_pdf_filename(pdf_path.name)
            source_row = {
                "file_name": pdf_path.name,
                "file_path": str(pdf_path),
                "file_type": "PDF",
                "source_role": "PRIMARY",
                "source_profile": "PDF_PRICE_LIST",
                "optional_source": False,
                "file_hash": file_hash(pdf_path),
                "status": "OK",
                "page_count": len({table.get("page") for table in extracted["tables"]}),
                "table_count": len(extracted["tables"]),
                "row_count": len(extracted["price_rows"]),
                "error_message": None,
            }
            insert_source_file(conn, source_row)
            insert_pdf_raw(conn, extracted["raw_rows"])
            all_price_rows.extend(extracted["price_rows"])
            all_products.extend(
                {
                    "product_code": code,
                    "product_name": parsed.get("product_name"),
                    "supplier": parsed.get("supplier"),
                    "alias_name": None,
                    "source_file": pdf_path.name,
                    "active": 1,
                }
                for code in (parsed.get("product_codes") or [None])
            )
            stats["pdf_files"] += 1
            stats["raw_pdf_rows"] += len(extracted["raw_rows"])
        except Exception as exc:  # noqa: BLE001 - logged into import status for user review
            stats["errors"].append(f"{pdf_path.name}: {exc}")
            insert_source_file(
                conn,
                {
                    "file_name": pdf_path.name,
                    "file_path": str(pdf_path),
                    "file_type": "PDF",
                    "source_role": "PRIMARY",
                    "source_profile": "PDF_PRICE_LIST",
                    "optional_source": False,
                    "status": "FAILED",
                    "error_message": str(exc),
                },
            )

    excel_files = [Path(item) for item in (excel_files or []) if str(item).strip()]
    for excel_path in excel_files:
        try:
            imported = import_excel_workbook(excel_path, import_batch_id=batch_id)
            profile = imported["profile"]
            insert_source_file(
                conn,
                {
                    "file_name": excel_path.name,
                    "file_path": str(excel_path),
                    "file_type": "EXCEL",
                    "source_role": "OPTIONAL_REFERENCE",
                    "source_profile": profile.get("profile_code"),
                    "optional_source": True,
                    "file_hash": file_hash(excel_path),
                    "status": "OK",
                    "page_count": imported.get("sheet_count"),
                    "table_count": None,
                    "row_count": len(imported["price_rows"]),
                    "error_message": None,
                },
            )
            all_price_rows.extend(imported["price_rows"])
            insert_excel_raw(conn, imported["raw_rows"])
            insert_products(conn, imported["products"])
            insert_colour_reference(conn, imported["colour_reference"])
            stats["excel_files"] += 1
            stats["raw_excel_rows"] += len(imported["raw_rows"])
        except Exception as exc:  # noqa: BLE001
            stats["errors"].append(f"{excel_path.name}: {exc}")
            insert_source_file(
                conn,
                {
                    "file_name": excel_path.name,
                    "file_path": str(excel_path),
                    "file_type": "EXCEL",
                    "source_role": "OPTIONAL_REFERENCE",
                    "source_profile": "UNKNOWN_EXCEL",
                    "optional_source": True,
                    "status": "FAILED",
                    "error_message": str(exc),
                },
            )

    mark_version_conflicts(all_price_rows)
    mark_duplicate_price_conflicts(all_price_rows)
    stats["price_rows"] = insert_prices(conn, all_price_rows)
    insert_products(conn, all_products)
    stats.update(get_summary(conn))
    conn.close()
    return stats


def get_prices(filters: dict | None = None, db_path: str | Path | None = None, limit: int | None = 500) -> list[dict]:
    conn = open_database(db_path)
    try:
        return query_prices(conn, filters=filters or {}, limit=limit)
    finally:
        conn.close()


def get_table(table: str, db_path: str | Path | None = None, limit: int | None = 500) -> list[dict]:
    conn = open_database(db_path)
    try:
        return query_table(conn, table, limit=limit)
    finally:
        conn.close()


def get_dashboard_summary(db_path: str | Path | None = None) -> dict:
    conn = open_database(db_path)
    try:
        return get_summary(conn)
    finally:
        conn.close()


def export_current(filters: dict | None = None, db_path: str | Path | None = None, output_folder: str | Path | None = None) -> Path:
    config = load_config()
    conn = open_database(db_path)
    try:
        folder = resolve_project_path(output_folder or config["export_folder"])
        return export_workbook(conn, folder, filters=filters or {})
    finally:
        conn.close()
