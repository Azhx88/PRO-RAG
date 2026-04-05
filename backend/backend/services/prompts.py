"""
Prompt templates for the SQL pipeline.

Ported and adapted from the previous `rag` project's prompts.py.
Centralises all LLM prompt strings so they are easy to maintain and test.
"""


# ─── Text-to-SQL Prompt ───────────────────────────────────────
TEXT_TO_SQL_PROMPT = """PostgreSQL expert. Convert question to SQL.

{available_tables_header}

SCHEMA:
{schema_text}

{conversation_context}

QUESTION: {user_question}

{error_context}

RULES:
- Return ONLY complete SQL ending with semicolon (;)
- ONLY use tables/columns listed in SCHEMA. NEVER invent names.
- ALWAYS wrap table names in double quotes exactly as they appear.
- ALWAYS wrap column names in double quotes using the EXACT names from the schema.
- One table = no JOINs. Multiple tables = use JOINs only when foreign keys exist.
- TEXT columns with numeric values: ALWAYS filter before CAST. Use: WHERE CAST("col" AS TEXT) ~ '^[0-9]+(\\.[0-9]+)?$' AND then CAST("col" AS NUMERIC). NEVER cast TEXT to NUMERIC without a regex filter — data may contain non-numeric values like '.', 'Hold', or empty strings.
- Add LIMIT 100 unless user wants all rows.
- Map casual / approximate terms to the closest matching column from the schema.
- SELECT only (no DELETE/DROP/INSERT/UPDATE).
- "top performers" or "best" means ORDER BY DESC; "bottom" or "worst" means ORDER BY ASC.
- When sorting or aggregating TEXT columns that contain numbers, ALWAYS add a WHERE clause that filters out non-numeric rows BEFORE using CAST or ORDER BY (e.g., WHERE CAST("col" AS TEXT) ~ '^[0-9]+(\\.[0-9]+)?$').

SQL:
"""


# ─── Explain Results Prompt ────────────────────────────────────
EXPLAIN_RESULTS_PROMPT = """Question: {user_question}
SQL: {sql_query}
Results:
{query_results}

Answer the question in 2-3 sentences based on the data. Be concise.
Highlight key numbers, trends, or anomalies.
"""


# ─── Builder functions ─────────────────────────────────────────

def build_available_tables_header(table_names: list[str]) -> str:
    """Build a prominent AVAILABLE TABLES header to prevent hallucinated names."""
    lines = [
        "=" * 50,
        "AVAILABLE TABLES (ONLY these tables exist):",
    ]
    for t in table_names:
        lines.append(f'  • "{t}"')
    lines.append("")
    lines.append("WARNING: Do NOT reference any table not listed above.")
    lines.append("WARNING: Do NOT invent or guess table names.")
    if len(table_names) == 1:
        lines.append(
            f'NOTE: There is only ONE table ("{table_names[0]}"). '
            "Do NOT use JOINs."
        )
    lines.append("=" * 50)
    return "\n".join(lines)


def build_text_to_sql_prompt(
    schema_text: str,
    user_question: str,
    table_names: list[str],
    previous_error: str | None = None,
    conversation_context: str = "",
) -> str:
    """Assemble the full Text-to-SQL prompt."""
    error_context = ""
    if previous_error:
        error_context = (
            f"PREVIOUS ATTEMPT FAILED with error: {previous_error}\n"
            "Fix the issue in this attempt. Use ONLY the exact column "
            "and table names listed in the schema above."
        )

    conv_section = ""
    if conversation_context:
        conv_section = f"RECENT CONTEXT:\n{conversation_context}\nUse above context for follow-up questions. Ignore if independent.\n"

    return TEXT_TO_SQL_PROMPT.format(
        available_tables_header=build_available_tables_header(table_names),
        schema_text=schema_text,
        user_question=user_question,
        error_context=error_context,
        conversation_context=conv_section,
    )


def build_explain_results_prompt(
    user_question: str,
    sql_query: str,
    query_results: str,
) -> str:
    """Build a prompt asking the LLM to explain query results."""
    return EXPLAIN_RESULTS_PROMPT.format(
        user_question=user_question,
        sql_query=sql_query,
        query_results=query_results,
    )
