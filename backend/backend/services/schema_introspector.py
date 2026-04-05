"""
Schema Introspector — Reads live PostgreSQL metadata for workspace tables.

Ported from the previous `rag` project's database.py + schema_analyzer.py,
adapted to use SQLAlchemy Session objects instead of raw psycopg2 connections.
"""

import logging
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_table_columns(db: Session, table_name: str) -> list[dict[str, Any]]:
    """
    Query information_schema for the actual PostgreSQL column metadata.

    Returns a list of dicts:
      [{"column_name": "price", "data_type": "numeric", "is_nullable": "YES", ...}, ...]
    """
    result = db.execute(text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
        ORDER BY ordinal_position;
    """), {"table_name": table_name})

    columns = [dict(row._mapping) for row in result]
    logger.info(f"Introspected {len(columns)} columns for table '{table_name}'")
    return columns


def get_sample_data(
    db: Session,
    table_name: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch sample rows from a PostgreSQL table.

    The table_name MUST already have been validated as existing.
    Values are serialised to strings so they are always JSON-safe.
    """
    result = db.execute(
        text(f'SELECT * FROM "{table_name}" LIMIT :limit'),
        {"limit": limit},
    )
    columns = list(result.keys())
    rows = result.fetchall()

    clean_rows = []
    for row in rows:
        clean_row = {}
        for col, value in zip(columns, row):
            clean_row[col] = str(value) if value is not None else None
        clean_rows.append(clean_row)

    return clean_rows


def get_row_count(db: Session, table_name: str) -> int:
    """Return the total row count for a table."""
    try:
        result = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        return result.scalar() or 0
    except Exception:
        return 0


def introspect_workspace_tables(
    db: Session,
    schema_json: dict,
) -> dict:
    """
    For each table in a workspace's schema_json, fetch the actual PostgreSQL
    metadata and enrich the schema with live column info + sample data.

    This ensures the schema sent to the LLM always matches the real database,
    even if column names were sanitised during upload.

    Returns a new schema_json dict (original is not mutated).
    """
    enriched = {"sheets": [], "file_type": schema_json.get("file_type", "excel")}

    for sheet in schema_json.get("sheets", []):
        table_name = sheet.get("table_name", sheet.get("sheet_name"))
        if not table_name:
            continue

        # Get real columns from PostgreSQL
        pg_columns = get_table_columns(db, table_name)

        if pg_columns:
            # Use live database metadata
            enriched_columns = []
            for pg_col in pg_columns:
                # Try to find matching original column info for extra context
                original_info = _find_original_column(
                    pg_col["column_name"],
                    sheet.get("columns", []),
                )
                enriched_columns.append({
                    "name": pg_col["column_name"],
                    "dtype": pg_col["data_type"],
                    "is_nullable": pg_col["is_nullable"],
                    "original_name": original_info.get("original_name", "")
                        if original_info else "",
                    "sample_values": original_info.get("sample_values", [])
                        if original_info else [],
                })

            # Get sample data directly from PostgreSQL
            sample_rows = get_sample_data(db, table_name, limit=3)
            # Backfill sample_values from live data if missing
            if sample_rows:
                for col_info in enriched_columns:
                    if not col_info["sample_values"]:
                        col_info["sample_values"] = [
                            row.get(col_info["name"], "")
                            for row in sample_rows[:3]
                            if row.get(col_info["name"]) is not None
                        ]

            row_count = get_row_count(db, table_name)
        else:
            # Table doesn't exist in PG yet — fall back to stored schema
            enriched_columns = sheet.get("columns", [])
            row_count = sheet.get("row_count", 0)

        enriched["sheets"].append({
            "sheet_name": sheet.get("sheet_name", table_name),
            "table_name": table_name,
            "columns": enriched_columns,
            "row_count": row_count,
        })

    return enriched


def _find_original_column(
    pg_col_name: str,
    schema_columns: list[dict],
) -> dict | None:
    """Find the matching column entry in the stored schema by name."""
    for col in schema_columns:
        if col.get("name", "").lower() == pg_col_name.lower():
            return col
        # Also check original_name
        if col.get("original_name", "").lower() == pg_col_name.lower():
            return col
    return None
