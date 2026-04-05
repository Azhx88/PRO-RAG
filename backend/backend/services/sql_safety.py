"""
SQL Safety — Validates and extracts SQL from LLM responses.

Ported from the previous working `rag` project's QueryEngine._is_safe_sql()
and _extract_sql() methods, adapted for the hybrid-rag architecture.
"""

import re
from typing import Optional, Tuple

# Keywords that indicate modifying / destructive SQL
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT",
    "UPDATE", "CREATE", "GRANT", "REVOKE", "EXEC",
    "EXECUTE", "MERGE",
]


def is_safe_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """
    Check whether a SQL query is safe to execute.

    Only SELECT / WITH (CTE) queries are allowed.
    Returns (True, None) if safe, or (False, reason) if unsafe.
    """
    sql_upper = sql.upper().strip()

    # Must start with SELECT or WITH (for CTEs)
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return False, "Query must start with SELECT or WITH"

    # Check for dangerous keywords using word-boundary regex
    for keyword in DANGEROUS_KEYWORDS:
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Dangerous keyword '{keyword}' detected"

    # Reject multi-statement SQL (semicolon in the middle)
    # Allow a single trailing semicolon
    if ";" in sql.rstrip(";"):
        return False, "Multiple statements not allowed"

    return True, None


def extract_sql(response: str) -> Optional[str]:
    """
    Extract a clean SQL query from an LLM response.

    Uses multiple strategies in order of priority:
      1. Extract from ```sql ... ``` code blocks
      2. Find SELECT ... ; pattern via regex
      3. Use the raw response if it starts with SELECT

    Returns the extracted SQL string, or None if nothing was found.
    """
    if not response:
        return None

    # Strategy 1: Extract from fenced code block
    code_block = re.search(
        r"```(?:sql)?\s*\n?(.*?)\n?```",
        response,
        re.DOTALL | re.IGNORECASE,
    )
    if code_block:
        sql = code_block.group(1).strip()
        if sql:
            return sql

    # Strategy 2: Find a SELECT statement
    select_match = re.search(
        r"(SELECT\s+.+?)(?:;|$)",
        response,
        re.DOTALL | re.IGNORECASE,
    )
    if select_match:
        sql = select_match.group(1).strip()
        # Stop at common English words that follow SQL
        for stop_word in ["\n\nThis", "\n\nThe", "\n\nNote",
                          "\n\nExplanation", "\n\nHere"]:
            if stop_word in sql:
                sql = sql[:sql.index(stop_word)]
        return sql.strip()

    # Strategy 3: If the response looks like SQL, use it directly
    cleaned = response.strip()
    if cleaned.upper().startswith("SELECT"):
        first_statement = cleaned.split(";")[0].strip()
        return first_statement

    return None
