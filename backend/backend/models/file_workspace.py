from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, func
from database import Base

class FileWorkspace(Base):
    __tablename__ = "file_workspaces"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "excel", "csv", "pdf", "text"
    file_path = Column(String, nullable=False)
    schema_json = Column(JSON, nullable=True)   # For structured files
    table_name = Column(String, nullable=True)  # PostgreSQL table for Excel/CSV data
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
