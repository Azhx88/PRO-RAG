from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models.user import User
from models.chat import ChatSession, ChatMessage
from utils.auth_utils import get_current_user
from services.excel_exporter import ExportManager
from services.sql_retriever import execute_sql
from models.file_workspace import FileWorkspace
import os
from config import settings

router = APIRouter(prefix="/export", tags=["export"])

class ExportRequest(BaseModel):
    session_id: int
    workspace_id: int

@router.post("/excel")
def export_excel(
    req: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = db.query(FileWorkspace).filter(
        FileWorkspace.id == req.workspace_id,
        FileWorkspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == req.session_id,
        ChatMessage.role == "assistant"
    ).order_by(ChatMessage.created_at.desc()).all()

    last_insights = ""
    chart_path = None
    last_query = ""
    table_data = []
    sql = ""

    for msg in messages:
        if not last_insights:
            last_insights = msg.content
        if msg.meta and msg.meta.get("chart_path") and not chart_path:
            chart_path = msg.meta["chart_path"]
        if msg.meta and msg.meta.get("results_preview") and not table_data:
            table_data = msg.meta["results_preview"]
            sql = msg.meta.get("sql", "")
            if sql:
                try:
                    table_data = execute_sql(sql, db)
                except:
                    pass

    user_message = db.query(ChatMessage).filter(
        ChatMessage.session_id == req.session_id,
        ChatMessage.role == "user"
    ).order_by(ChatMessage.created_at.desc()).first()
    
    question_text = user_message.content if user_message else "Chat Export"

    manager = ExportManager()
    filename = manager.create_dashboard_excel(
        question=question_text,
        sql=sql,
        results=table_data,
        insight=last_insights,
        chart_filename=os.path.basename(chart_path) if chart_path else None
    )
    
    export_path = os.path.join(manager.export_dir, filename)
    return FileResponse(
        path=export_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/powerbi")
def export_powerbi(
    req: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = db.query(FileWorkspace).filter(
        FileWorkspace.id == req.workspace_id,
        FileWorkspace.user_id == current_user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == req.session_id,
        ChatMessage.role == "assistant"
    ).order_by(ChatMessage.created_at.desc()).all()

    last_insights = ""
    table_data = []
    sql = ""

    for msg in messages:
        if not last_insights:
            last_insights = msg.content
        if msg.meta and msg.meta.get("results_preview") and not table_data:
            table_data = msg.meta["results_preview"]
            sql = msg.meta.get("sql", "")
            if sql:
                try:
                    table_data = execute_sql(sql, db)
                except:
                    pass

    manager = ExportManager()
    filename = manager.create_powerbi_excel(
        question="Power BI Export",
        sql=sql,
        results=table_data,
        insight=last_insights
    )
    
    export_path = os.path.join(manager.export_dir, filename)
    return FileResponse(
        path=export_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
