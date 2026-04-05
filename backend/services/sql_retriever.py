"""
SQL Retriever — Generates, validates, fixes, and executes SQL queries.

Integrates:
  - sql_safety.py      — blocks destructive SQL, extracts clean SQL from LLM
  - prompts.py         — structured prompt templates
  - schema_introspector — live PostgreSQL schema introspection
  - rag_context.py     — keyword-based table relevance matching
"""

import json
import logging
import re
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.llm_service import call_groq
from services.sql_safety import is_safe_sql, extract_sql
from services.prompts import build_text_to_sql_prompt, build_explain_results_prompt
from services.schema_introspector import introspect_workspace_tables
from services.rag_context import get_focused_context

logger = logging.getLogger(__name__)


# ─── SQL string helpers ───────────────────────────────────────────────

def clean_sql(raw: str) -> str:
    """Strip markdown code fences and surrounding whitespace from LLM-generated SQL."""
    # First try the multi-strategy extractor
    extracted = extract_sql(raw)
    if extracted:
        return extracted
    # Fallback: simple strip
    cleaned = re.sub(r"```(?:sql)?\s*", "", raw)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()


def schema_to_prompt(schema_json: dict) -> str:
    """Convert schema JSON to a compact LLM-readable format (full dump, no filtering)."""
    lines = []
    for sheet in schema_json.get("sheets", []):
        table = sheet.get("table_name", sheet["sheet_name"])
        lines.append(f'Table: "{table}"')
        for col in sheet.get("columns", []):
            original = col.get("original_name", "")
            hint = f" (originally: {original})" if original and original != col["name"] else ""
            samples = col.get("sample_values", [])[:2]
            dtype = col.get("dtype", col.get("data_type", "text"))
            lines.append(f'  - "{col["name"]}" ({dtype}){hint} — samples: {samples}')
    return "\n".join(lines)


def get_table_names(schema_json: dict) -> list[str]:
    """Extract all table names from the workspace schema."""
    tables = []
    for sheet in schema_json.get("sheets", []):
        tables.append(sheet.get("table_name", sheet["sheet_name"]))
    return tables


# ─── SQL Generation ───────────────────────────────────────────────────

def generate_sql(
    query: str,
    schema_json: dict,
    previous_error: str = None,
    conversation_history: list[dict] = None,
    db: Session = None,
) -> str:
    """
    Generate a SQL query from a natural language question.

    Enriches the schema with live PostgreSQL metadata when a db session
    is available, and uses RAG context to select only relevant tables.
    """
    # Enrich schema with live DB introspection if possible
    working_schema = schema_json
    if db is not None:
        try:
            working_schema = introspect_workspace_tables(db, schema_json)
        except Exception as e:
            logger.warning(f"Schema introspection failed, using stored schema: {e}")

    # Use RAG context to get focused schema (only relevant tables)
    focused_schema_str, relevant_tables = get_focused_context(query, working_schema)

    # If RAG returned all tables or no tables, fall back to full schema
    all_tables = get_table_names(working_schema)
    if not relevant_tables:
        relevant_tables = all_tables
        focused_schema_str = schema_to_prompt(working_schema)

    # Build conversation context
    conv_context = ""
    if conversation_history:
        conv_lines = []
        for conv in conversation_history:
            conv_lines.append(f"  Q: {conv.get('question', '')}")
            if conv.get('sql'):
                conv_lines.append(f"  SQL: {conv['sql']}")
        conv_context = "\n".join(conv_lines)

    # Build prompt using structured template
    prompt = build_text_to_sql_prompt(
        schema_text=focused_schema_str,
        user_question=query,
        table_names=relevant_tables,
        previous_error=previous_error,
        conversation_context=conv_context,
    )

    return call_groq(
        prompt,
        system=(
            "You are a SQL query generator. Return only valid PostgreSQL SQL. "
            "Always use exact table and column names from the schema. "
            "Never refuse — map user terms to the closest column."
        ),
    )


# ─── Table / column name fixing ──────────────────────────────────────

def fix_table_names(sql: str, schema_json: dict) -> str:
    """Auto-correct table names in SQL to match the actual schema."""
    actual_tables = []
    for sheet in schema_json.get("sheets", []):
        actual_tables.append(sheet.get("table_name", sheet["sheet_name"]))

    allowed_lower = {t.lower() for t in actual_tables}

    # Extract referenced table names (quoted and unquoted)
    quoted_refs = re.finditer(r'(?:FROM|JOIN)\s+"([^"]+)"', sql, re.IGNORECASE)
    unquoted_refs = re.finditer(r'(?:FROM|JOIN)\s+([a-zA-Z_]\w*)', sql, re.IGNORECASE)

    replacements = []
    for m in list(quoted_refs) + list(unquoted_refs):
        ref = m.group(1)
        if ref.lower() in allowed_lower:
            continue

        match = _find_best_table_match(ref, actual_tables)
        if match:
            old_fragment = m.group(0)
            keyword = old_fragment.split()[0]
            new_fragment = f'{keyword} "{match}"'
            replacements.append((old_fragment, new_fragment))

    # If no match found but there's only one table, use it
    if not replacements:
        all_refs = (
            re.findall(r'(?:FROM|JOIN)\s+"([^"]+)"', sql, re.IGNORECASE)
            + re.findall(r'(?:FROM|JOIN)\s+([a-zA-Z_]\w*)', sql, re.IGNORECASE)
        )
        bad_refs = [r for r in all_refs if r.lower() not in allowed_lower]
        if bad_refs and len(actual_tables) == 1:
            for bad in bad_refs:
                sql = re.sub(
                    rf'(FROM|JOIN)\s+"?{re.escape(bad)}"?',
                    rf'\1 "{actual_tables[0]}"',
                    sql,
                    flags=re.IGNORECASE,
                )
            return sql

    for old, new in replacements:
        sql = sql.replace(old, new)

    return sql


def _find_best_table_match(ref: str, actual_tables: list[str]) -> str | None:
    """Find the best matching table for a misgenerated reference."""
    ref_lower = ref.lower()

    # 1. Case-insensitive exact match
    for t in actual_tables:
        if t.lower() == ref_lower:
            return t

    # 2. Reference is a substring of an actual table
    matches = [t for t in actual_tables if ref_lower in t.lower()]
    if len(matches) == 1:
        return matches[0]

    # 3. Actual table is a substring of the reference
    matches = [t for t in actual_tables if t.lower() in ref_lower]
    if len(matches) == 1:
        return matches[0]

    # 4. First word matches
    matches = [t for t in actual_tables if t.lower().split()[0] == ref_lower]
    if len(matches) == 1:
        return matches[0]

    # 5. Only one table exists
    if len(actual_tables) == 1:
        return actual_tables[0]

    return None


def _fuzzy_match_column(ref: str, all_columns: dict[str, str]) -> str | None:
    """Find the best matching column for a potentially misspelled reference."""
    ref_lower = ref.lower().strip()

    # 1. Exact case-insensitive match
    if ref_lower in all_columns:
        return all_columns[ref_lower]

    # 2. Common abbreviation/synonym mappings
    synonyms = {
        "cgpa": ["gpa", "grade_point", "grade"],
        "marks": ["score", "total_marks", "mark", "total_score"],
        "name": ["student_name", "full_name", "first_name", "employee_name"],
        "id": ["student_id", "emp_id", "employee_id", "roll_no", "roll"],
        "phone": ["phone_number", "mobile", "contact", "mobile_number"],
        "email": ["email_id", "email_address", "mail"],
        "addr": ["address", "location", "city"],
        "dept": ["department", "dept_name"],
        "avg": ["average"],
        "pct": ["percentage", "percent"],
        "attendance": ["attendance_percentage", "attendance_rate"],
        "dob": ["date_of_birth", "birth_date"],
    }
    for canonical, syns in synonyms.items():
        all_terms = [canonical] + syns
        if ref_lower in all_terms:
            for term in all_terms:
                if term in all_columns:
                    return all_columns[term]

    # 3. ref is a substring of a column name
    matches = [name for lower, name in all_columns.items() if ref_lower in lower]
    if len(matches) == 1:
        return matches[0]

    # 4. Column name is a substring of ref
    matches = [name for lower, name in all_columns.items() if lower in ref_lower]
    if len(matches) == 1:
        return matches[0]

    # 5. Starts-with or ends-with match
    matches = [name for lower, name in all_columns.items()
               if lower.startswith(ref_lower) or ref_lower.startswith(lower)
               or lower.endswith(ref_lower) or ref_lower.endswith(lower)]
    if len(matches) == 1:
        return matches[0]

    return None


def _sanitize_col_name(name: str) -> str:
    """Apply the same sanitization used when loading data to PostgreSQL."""
    return re.sub(r'[^a-z0-9]', '_', name.lower().strip())


def fix_column_names(sql: str, schema_json: dict) -> str:
    """Auto-correct column names in SQL to match the actual PostgreSQL columns."""
    pg_columns = {}
    fuzzy_columns = {}
    table_names_lower = set()

    for sheet in schema_json.get("sheets", []):
        table_names_lower.add(sheet.get("table_name", sheet["sheet_name"]).lower())
        for col in sheet.get("columns", []):
            schema_name = col.get("name", "")
            sanitized = _sanitize_col_name(schema_name)
            pg_columns[sanitized] = sanitized
            fuzzy_columns[schema_name.lower()] = sanitized
            original = col.get("original_name", "")
            if original:
                fuzzy_columns[original.lower()] = sanitized

    # Fix quoted column references
    quoted_refs = re.findall(r'"([^"]+)"', sql)
    for ref in quoted_refs:
        if ref.lower() in table_names_lower:
            continue

        sanitized_ref = _sanitize_col_name(ref)

        if sanitized_ref in pg_columns:
            if ref != sanitized_ref:
                sql = sql.replace(f'"{ref}"', f'"{sanitized_ref}"')
            continue

        match = _fuzzy_match_column(ref, fuzzy_columns)
        if match:
            sql = sql.replace(f'"{ref}"', f'"{match}"')

    return sql


# ─── Safe CAST filter ─────────────────────────────────────────────────

def _get_text_columns(schema_json: dict) -> set[str]:
    """Return all column names that are stored as text/varchar in PostgreSQL."""
    text_cols = set()
    for sheet in schema_json.get("sheets", []):
        for col in sheet.get("columns", []):
            dtype = col.get("dtype", col.get("data_type", "")).lower()
            if dtype in ("text", "character varying", "varchar"):
                text_cols.add(col.get("name", "").lower())
    return text_cols


def safe_cast_filter(sql: str, schema_json: dict = None) -> str:
    """
    Auto-inject a regex WHERE filter when CAST("col" AS NUMERIC) is used
    on a text column that may contain non-numeric values like '.', 'Hold', ''.

    Only applies to columns known to be text type from the schema.
    """
    if not schema_json:
        return sql

    text_cols = _get_text_columns(schema_json)
    if not text_cols:
        return sql

    # Find all CAST("col" AS NUMERIC/INTEGER/...) patterns
    cast_matches = re.findall(
        r'CAST\(\s*"([^"]+)"\s+AS\s+(?:NUMERIC|INTEGER|FLOAT|DECIMAL|BIGINT)\s*\)',
        sql,
        re.IGNORECASE,
    )

    # Filter to only text columns that need the guard
    cols_needing_filter = set()
    for col_name in cast_matches:
        if col_name.lower() in text_cols:
            cols_needing_filter.add(col_name)

    if not cols_needing_filter:
        return sql

    # Build regex filter: CAST("col" AS TEXT) ~ '^[0-9]+(\.[0-9]+)?$'
    # This matches only valid integers and decimals, rejecting '.', 'Hold', '', etc.
    # We cast to TEXT first to prevent PostgreSQL crashes if the column is already numeric (double precision)
    numeric_regex = "'^[0-9]+(\\.[0-9]+)?$'"
    filter_parts = []
    for col in cols_needing_filter:
        filter_parts.append('CAST("' + col + '" AS TEXT) ~ ' + numeric_regex)
    filter_clause = " AND ".join(filter_parts)

    # Determine if there's already a WHERE clause
    has_where = bool(re.search(r'\bWHERE\b', sql, re.IGNORECASE))

    # Find where to insert: before ORDER BY / GROUP BY / LIMIT / HAVING
    insert_pos = None
    for keyword in ['ORDER BY', 'GROUP BY', 'LIMIT', 'HAVING']:
        pattern = re.compile(r'\b' + keyword + r'\b', re.IGNORECASE)
        m = pattern.search(sql)
        if m:
            insert_pos = m.start()
            break

    prefix = "AND " if has_where else "WHERE "

    if insert_pos is not None:
        sql = sql[:insert_pos] + prefix + filter_clause + " " + sql[insert_pos:]
    else:
        sql = sql.rstrip(";").rstrip() + " " + prefix + filter_clause + ";"

    logger.info(f"SQL after safe_cast_filter: {sql}")
    return sql


# ─── SQL Execution ────────────────────────────────────────────────────

def execute_sql(sql: str, db: Session, schema_json: dict = None) -> list[dict]:
    """
    Clean, validate, fix, and execute a SQL query.

    Safety: blocks destructive SQL (DROP, DELETE, INSERT, etc.)
    """
    sql = clean_sql(sql)
    logger.info(f"SQL after clean: {sql}")

    # Safety check — block dangerous queries
    safe, reason = is_safe_sql(sql)
    if not safe:
        raise ValueError(f"Blocked unsafe SQL: {reason}")

    if schema_json:
        sql = fix_table_names(sql, schema_json)
        sql = fix_column_names(sql, schema_json)
        sql = safe_cast_filter(sql, schema_json)
        logger.info(f"SQL after all fixes: {sql}")

    try:
        result = db.execute(text(sql))
        columns = list(result.keys())
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"SQL execution failed: {sql} | Error: {str(e)}")
        db.rollback()
        raise ValueError(f"SQL execution failed: {str(e)}")


# ─── Insight Generation ──────────────────────────────────────────────

def generate_insights(query: str, sql: str, results: list[dict]) -> str:
    results_preview = json.dumps(results[:20], default=str, indent=2)
    prompt = build_explain_results_prompt(
        user_question=query,
        sql_query=sql,
        query_results=results_preview,
    )
    return call_groq(
        prompt,
        system="You are a data analyst providing insights from SQL query results.",
    )
