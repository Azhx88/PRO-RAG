from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, func
from database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("file_workspaces.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Integer, default=1)  # 1=active, 0=history

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    meta = Column("metadata", JSON, nullable=True)  # chart_path, sql_query, sources etc.
    created_at = Column(DateTime, server_default=func.now())
