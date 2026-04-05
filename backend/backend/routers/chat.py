from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from collections import deque
import logging
from database import get_db
from models.user import User
from models.file_workspace import FileWorkspace
from models.chat import ChatSession, ChatMessage
from utils.auth_utils import get_current_user
from services.query_router import detect_intent, is_greeting
from services.sql_retriever import generate_sql, execute_sql, generate_insights
from services.vector_retriever import retrieve_chunks, generate_rag_response
from services.chart_generator import generate_chart, detect_chart_type
from services.llm_service import call_groq
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# ─── Conversation Memory ─────────────────────────────────────────────
# Per-session memory of the last 3 Q&A pairs so follow-up questions work.
# Key: session_id → deque of {question, sql, row_count, columns}
_conversation_memory: dict[int, deque] = {}

MAX_MEMORY = 3  # Keep last 3 exchanges


def _get_memory(session_id: int) -> list[dict]:
    """Return the conversation history for a session (list of dicts)."""
    return list(_conversation_memory.get(session_id, []))


def _save_to_memory(session_id: int, question: str, sql: str, results: list[dict]):
    """Append a Q&A pair to the session's conversation memory."""
    if session_id not in _conversation_memory:
        _conversation_memory[session_id] = deque(maxlen=MAX_MEMORY)
    _conversation_memory[session_id].append({
        "question": question,
        "sql": sql,
        "row_count": len(results) if results else 0,
        "columns": list(results[0].keys()) if results else [],
    })


def _load_memory_from_db(session_id: int, db: Session):
    """Rehydrate conversation memory from DB for a resumed session."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    _conversation_memory[session_id] = deque(maxlen=MAX_MEMORY)
    prev_user_content = None
    for msg in messages:
        if msg.role == "user":
            prev_user_content = msg.content
        elif msg.role == "assistant" and msg.meta:
            mode = msg.meta.get("mode", "")
            sql = msg.meta.get("sql", "")
            if mode in ("sql", "sql_retry") and sql and prev_user_content:
                _conversation_memory[session_id].append({
                    "question": prev_user_content,
                    "sql": sql,
                    "row_count": msg.meta.get("row_count", 0),
                    "columns": list((msg.meta.get("results_preview") or [{}])[0].keys()),
                })


class ChatRequest(BaseModel):
    workspace_id: int
    query: str
    session_id: Optional[int] = None

@router.post("/message")
def send_message(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify workspace belongs to user
    workspace = db.query(FileWorkspace).filter(
        FileWorkspace.id == req.workspace_id,
        FileWorkspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get or create session
    if req.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
        # Rehydrate memory from DB if this session isn't already in memory
        if session and session.id not in _conversation_memory:
            _load_memory_from_db(session.id, db)
    else:
        session = ChatSession(user_id=current_user.id, workspace_id=req.workspace_id)
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=req.query)
    db.add(user_msg)
    db.commit()

    intent = detect_intent(req.query)
    response_metadata = {}
    chart_path = None
    sql_used = None
    answer = ""

    try:
        if workspace.file_type in ["excel", "csv"]:
            # Ensure schema_json has table_name set (fix for older workspaces)
            schema = workspace.schema_json or {}
            from services.file_processor import sanitize_table_name
            for sheet in schema.get("sheets", []):
                if not sheet.get("table_name"):
                    sheet["table_name"] = workspace.table_name or sanitize_table_name(current_user.id, workspace.filename, sheet.get("sheet_name", "main"))

            if not intent["is_data_query"]:
                # General chat — respond without SQL
                answer = call_groq(
                    req.query,
                    system="You are a helpful data assistant. The user has uploaded a spreadsheet. "
                           "Answer their general message naturally. If they seem to want data, "
                           "suggest they ask a specific question about their data.",
                )
                response_metadata["mode"] = "general_chat"
            else:
                # SQL retrieval path with conversation memory
                conversation_history = _get_memory(session.id)

                try:
                    sql = generate_sql(
                        req.query,
                        schema,
                        conversation_history=conversation_history,
                        db=db,
                    )
                    sql_used = sql
                    results = execute_sql(sql, db, schema_json=schema)
                    insights = generate_insights(req.query, sql, results)
                    answer = insights
                    response_metadata["sql"] = sql
                    response_metadata["row_count"] = len(results)
                    response_metadata["results_preview"] = json.loads(json.dumps(results[:10], default=str))
                    response_metadata["mode"] = "sql"

                    # Save to conversation memory for follow-up questions
                    _save_to_memory(session.id, req.query, sql, results)

                except (ValueError, Exception) as first_error:
                    # Retry with error context so the LLM can fix its mistake
                    try:
                        sql = generate_sql(
                            req.query,
                            schema,
                            previous_error=str(first_error),
                            conversation_history=conversation_history,
                            db=db,
                        )
                        sql_used = sql
                        results = execute_sql(sql, db, schema_json=schema)
                        insights = generate_insights(req.query, sql, results)
                        answer = insights
                        response_metadata["sql"] = sql
                        response_metadata["row_count"] = len(results)
                        response_metadata["results_preview"] = json.loads(json.dumps(results[:10], default=str))
                        response_metadata["mode"] = "sql_retry"

                        # Save successful retry to memory
                        _save_to_memory(session.id, req.query, sql, results)

                    except (ValueError, Exception) as e:
                        # Both attempts failed — give a direct answer
                        tables_info = []
                        for s in schema.get("sheets", []):
                            t_name = s.get("table_name", s["sheet_name"])
                            cols = [c["name"] for c in s.get("columns", [])]
                            tables_info.append(f'Table "{t_name}" — columns: {", ".join(cols)}')
                        schema_hint = "\n".join(tables_info)
                        answer = call_groq(
                            f'The user asked: "{req.query}"\n\n'
                            f"Your data has:\n{schema_hint}\n\n"
                            "I could not run a SQL query. Answer the user's question as best you can "
                            "using ONLY the column/table information above. Tell them what data is "
                            "available and give a direct, helpful answer. Do NOT tell them to rephrase "
                            "or ask a different question — just answer with what you know.",
                            system="You are a helpful data assistant. NEVER tell the user to rephrase, "
                                   "reword, or ask a different question. NEVER say a term is 'unclear'. "
                                   "Just answer directly with what you know from the available data. "
                                   "Be concise and helpful.",
                        )
                        response_metadata["mode"] = "sql_fallback"
                        response_metadata["error"] = str(e)

                # Chart generation if dashboard intent
                if intent["wants_dashboard"] and response_metadata.get("mode") in ("sql", "sql_retry") and response_metadata.get("results_preview"):
                    try:
                        chart_path = generate_chart(req.query, results, schema)
                        response_metadata["chart_path"] = chart_path
                        response_metadata["has_chart"] = True
                    except Exception as chart_err:
                        logger.error(f"Chart generation failed: {chart_err}")

                # If user just wants a chart re-render (e.g. "show in bar chart")
                # and no SQL was generated, try to re-use the last successful query
                if intent["wants_dashboard"] and response_metadata.get("mode") not in ("sql", "sql_retry"):
                    memory = _get_memory(session.id)
                    if memory:
                        last = memory[-1]
                        last_sql = last.get("sql", "")
                        if last_sql:
                            try:
                                results = execute_sql(last_sql, db, schema_json=schema)
                                chart_path = generate_chart(req.query, results, schema)
                                response_metadata["chart_path"] = chart_path
                                response_metadata["has_chart"] = True
                                response_metadata["mode"] = "chart_rerender"
                                answer = f"Here's your data visualized as a {detect_chart_type(req.query)} chart."
                            except Exception as chart_err:
                                logger.error(f"Chart re-render failed: {chart_err}")
                                if not answer:
                                    answer = f"Could not generate chart: {str(chart_err)}"

        else:
            # Vector RAG path
            if is_greeting(req.query):
                # General greeting/chat — don't waste an embedding call
                answer = call_groq(
                    req.query,
                    system="You are a helpful assistant. The user has uploaded a document. "
                           "Answer their general message naturally. If they seem to want information "
                           "from the document, suggest they ask a specific question about it.",
                )
                response_metadata["mode"] = "general_chat"
            else:
                chunks = retrieve_chunks(req.query, req.workspace_id, db)
                answer = generate_rag_response(req.query, chunks)
                response_metadata["sources_count"] = len(chunks)
                response_metadata["sources"] = [
                    {"filename": c["filename"], "chunk_index": c["index"], "score": c["score"]}
                    for c in chunks
                ]

    except Exception as e:
        answer = f"Error processing your query: {str(e)}"

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer,
        meta=response_metadata
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "session_id": session.id,
        "answer": answer,
        "metadata": response_metadata,
        "file_type": workspace.file_type
    }

@router.get("/history/{workspace_id}")
def get_chat_history(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.workspace_id == workspace_id,
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()

    history = []
    for session in sessions:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).all()

        history.append({
            "session_id": session.id,
            "created_at": session.created_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.meta,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        })

    return history
