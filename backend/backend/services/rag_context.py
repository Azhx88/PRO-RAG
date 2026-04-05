"""
RAG Context — Keyword-based table relevance matching for the SQL pipeline.

Ported from the previous `rag` project's rag_context.py and adapted for
the hybrid-rag workspace schema format.

Instead of sending the ENTIRE schema to the LLM, this module identifies
which tables are most relevant to the user's question by keyword matching,
then returns a compact, focused schema string.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Synonym map — expands query words to cover common alternatives
SYNONYM_MAP = {
    "buy": ["order", "purchase"],
    "bought": ["order", "purchase"],
    "purchase": ["order", "buy"],
    "spend": ["amount", "total", "money"],
    "spent": ["amount", "total", "money"],
    "expensive": ["price", "cost", "amount"],
    "cheap": ["price", "cost", "amount"],
    "popular": ["count", "order", "quantity"],
    "top": ["most", "highest", "max"],
    "best": ["most", "highest", "max"],
    "worst": ["least", "lowest", "min"],
    "revenue": ["amount", "total", "sales"],
    "income": ["amount", "total", "sales"],
    "profit": ["amount", "total", "sales"],
    "sold": ["order", "quantity", "sales"],
    "selling": ["order", "quantity", "sales"],
    "student": ["name", "roll", "id"],
    "employee": ["name", "emp", "id"],
    "average": ["avg", "mean"],
    "percentage": ["pct", "percent"],
    "marks": ["score", "grade", "total"],
    "cgpa": ["gpa", "grade"],
}


def build_keyword_index(schema_json: dict) -> dict[str, dict[str, Any]]:
    """
    Build a keyword index from the workspace schema.

    For each table (sheet), collects keywords from:
      - table name + variations
      - column names (split on underscores)
      - data-type hints (numeric → money/price/amount, date → when/month/year)

    Returns:
      {
        "table_name": {
          "keywords": {"keyword1", "keyword2", ...},
          "columns": [...],
          "row_count": 100,
        },
        ...
      }
    """
    index: dict[str, dict[str, Any]] = {}

    for sheet in schema_json.get("sheets", []):
        table_name = sheet.get("table_name", sheet.get("sheet_name", ""))
        if not table_name:
            continue

        keywords: set[str] = set()

        # 1. Table name and variations
        keywords.add(table_name.lower())
        if table_name.endswith("s"):
            keywords.add(table_name[:-1].lower())
        for part in re.split(r'[_\s]+', table_name):
            part_lower = part.lower()
            if part_lower:
                keywords.add(part_lower)
                if part_lower.endswith("s") and len(part_lower) > 2:
                    keywords.add(part_lower[:-1])

        # 2. Column names
        columns = sheet.get("columns", [])
        for col in columns:
            col_name = col.get("name", "").lower()
            keywords.add(col_name)
            for part in col_name.split("_"):
                if part:
                    keywords.add(part)

        # 3. Data-type-based keywords
        for col in columns:
            col_type = col.get("dtype", col.get("data_type", "")).lower()
            col_name = col.get("name", "").lower()

            if any(t in col_type for t in ("numeric", "decimal", "float", "int")):
                keywords.update([
                    "amount", "money", "price", "cost", "total",
                    "spend", "revenue", "sales", "sum", "count",
                ])
            if any(t in col_type for t in ("date", "timestamp", "time")):
                keywords.update([
                    "date", "time", "when", "recent", "latest",
                    "oldest", "month", "year", "day",
                ])
            if "email" in col_name:
                keywords.update(["email", "contact", "reach"])
            if "phone" in col_name:
                keywords.update(["phone", "call", "contact"])
            if any(t in col_name for t in ("address", "city", "state", "country")):
                keywords.update([
                    "address", "city", "location", "where", "live", "state",
                ])

        keywords.discard("")

        index[table_name] = {
            "keywords": keywords,
            "columns": columns,
            "row_count": sheet.get("row_count", 0),
        }

    logger.info(
        "Built keyword index for %d table(s): %s",
        len(index),
        list(index.keys()),
    )
    return index


def get_relevant_tables(
    question: str,
    keyword_index: dict[str, dict[str, Any]],
) -> list[str]:
    """
    Score each table by keyword overlap with the question and return
    the most relevant table names.

    If no table matches, returns ALL tables (better to have too much
    context than none at all).
    """
    if not keyword_index:
        return []

    # Extract words from the question
    question_words = set(re.findall(r'\w+', question.lower()))

    # Expand with synonyms
    expanded = set(question_words)
    for word in question_words:
        if word in SYNONYM_MAP:
            expanded.update(SYNONYM_MAP[word])

    # Score each table
    scores: dict[str, int] = {}
    for table_name, ctx in keyword_index.items():
        matches = expanded.intersection(ctx["keywords"])
        scores[table_name] = len(matches)

    # Tables with score > 0
    relevant = [t for t, s in scores.items() if s > 0]

    # If nothing matched, use all tables
    if not relevant:
        logger.info("No specific tables matched — using full schema")
        relevant = list(keyword_index.keys())

    # De-duplicate while preserving order
    return list(dict.fromkeys(relevant))


def format_relevant_schema(
    schema_json: dict,
    relevant_tables: list[str],
) -> str:
    """
    Build a compact, LLM-readable schema string for only the relevant tables.

    Includes column names, data types, sample values.
    """
    lines = []
    for sheet in schema_json.get("sheets", []):
        table_name = sheet.get("table_name", sheet.get("sheet_name", ""))
        if table_name not in relevant_tables:
            continue

        row_count = sheet.get("row_count", "?")
        lines.append(f"Table: \"{table_name}\" ({row_count} rows)")
        for col in sheet.get("columns", []):
            name = col.get("name", "")
            dtype = col.get("dtype", col.get("data_type", ""))
            original = col.get("original_name", "")
            hint = f" (originally: {original})" if original and original != name else ""
            samples = col.get("sample_values", [])[:2]
            lines.append(f'  - "{name}" ({dtype}){hint} — samples: {samples}')

    return "\n".join(lines)


def get_focused_context(
    question: str,
    schema_json: dict,
) -> tuple[str, list[str]]:
    """
    Main entry point.  Given a user question and the workspace schema,
    return (focused_schema_string, list_of_relevant_table_names).

    Use this in place of the old ``schema_to_prompt()`` which sent
    everything.
    """
    index = build_keyword_index(schema_json)
    relevant = get_relevant_tables(question, index)
    schema_str = format_relevant_schema(schema_json, relevant)
    return schema_str, relevant
