import re

DASHBOARD_KEYWORDS = [
    "dashboard", "chart", "graph", "plot", "visualize", "visualization",
    "bar chart", "pie chart", "line chart", "trend", "show me"
]

STRUCTURED_KEYWORDS = ["table", "row", "column", "sheet", "total", "sum", "average",
                        "count", "filter", "where", "group by", "max", "min"]

DATA_QUERY_KEYWORDS = [
    "how many", "how much", "total", "sum", "average", "count", "list",
    "show", "find", "get", "what is", "what are", "which", "top", "bottom",
    "highest", "lowest", "maximum", "minimum", "compare", "between",
    "greater", "less", "more than", "fewer", "percentage", "ratio",
    "sales", "revenue", "profit", "cost", "price", "quantity", "amount",
    "date", "month", "year", "week", "daily", "monthly", "yearly",
    "sort", "order", "rank", "group", "category", "filter", "where",
    "above", "below", "range", "distribution", "breakdown",
    "table", "row", "column", "sheet", "data", "record", "entry",
    "chart", "graph", "plot", "visualize", "trend", "dashboard",
]

GENERAL_CHAT_PATTERNS = [
    r"^(hi|hello|hey|greetings|good\s*(morning|afternoon|evening))[\s!.,?]*$",
    r"^(thanks|thank you|thx|ty)[\s!.,?]*$",
    r"^(bye|goodbye|see you|later)[\s!.,?]*$",
    r"^(yes|no|ok|okay|sure|yep|nope|yeah|nah)[\s!.,?]*$",
    r"^(who are you|what can you do|help me|what is this)[\s!.,?]*$",
    r"^(how are you|what'?s up|sup)[\s!.,?]*$",
]


def is_data_query(query: str) -> bool:
    """Determine whether a user query is asking about data or is general chat."""
    q = query.lower().strip()

    # Short greetings / general chat
    for pattern in GENERAL_CHAT_PATTERNS:
        if re.match(pattern, q, re.IGNORECASE):
            return False

    # Very short queries with no data keywords are likely general chat
    if len(q.split()) <= 2 and not any(kw in q for kw in DATA_QUERY_KEYWORDS):
        return False

    # Check for data-related keywords
    if any(kw in q for kw in DATA_QUERY_KEYWORDS):
        return True

    # Contains a number or comparison — likely a data query
    if re.search(r"\d+", q) or re.search(r"[><=!]+", q):
        return True

    # Contains a question word + enough length — likely asking about data
    if re.match(r"^(what|how|which|where|when|who|why)", q) and len(q.split()) >= 4:
        return True

    # Default: not a data query
    return False


def detect_intent(query: str) -> dict:
    q = query.lower()
    wants_dashboard = any(kw in q for kw in DASHBOARD_KEYWORDS)
    wants_sql_hint = any(kw in q for kw in STRUCTURED_KEYWORDS)
    return {
        "wants_dashboard": wants_dashboard,
        "wants_sql_hint": wants_sql_hint,
        "is_data_query": is_data_query(query),
    }

def is_greeting(query: str) -> bool:
    """
    Returns True only for pure social messages (hi, thanks, bye).
    Used by the vector RAG path — everything else should go to retrieval.
    """
    q = query.lower().strip()
    for pattern in GENERAL_CHAT_PATTERNS:
        if re.match(pattern, q, re.IGNORECASE):
            return True
    # Very short (1-2 words) with no question intent
    words = q.split()
    if len(words) <= 2 and "?" not in q and not any(
        q.startswith(w) for w in ("what", "who", "wt", "where", "when", "how", "why", "which", "is", "are", "does", "do", "can", "tell")
    ):
        return True
    return False


def auto_detect_file(query: str, workspaces: list) -> dict | None:
    """
    Try to match query to a file by filename keywords.
    Returns workspace dict or None.
    """
    q = query.lower()
    for ws in workspaces:
        name = ws["filename"].lower().replace("_", " ").replace("-", " ")
        words = name.split()
        if any(word in q for word in words if len(word) > 3):
            return ws
    return None
