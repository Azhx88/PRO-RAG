import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.file_workspace import FileWorkspace
from utils.auth_utils import get_current_user
from services.schema_extractor import extract_excel_schema, extract_csv_schema
from services.file_processor import load_excel_to_postgres, process_pdf, process_text_file
from config import settings

router = APIRouter(prefix="/files", tags=["files"])

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf", ".txt"}

def get_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".xlsx", ".xls"]: return "excel"
    if ext == ".csv": return "csv"
    if ext == ".pdf": return "pdf"
    if ext == ".txt": return "text"
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_type = get_file_type(file.filename)

    # User-specific upload directory
    user_dir = os.path.join(settings.upload_dir, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, file.filename)

    # Save file (overwrite if exists)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Check if workspace already exists — overwrite
    existing = db.query(FileWorkspace).filter(
        FileWorkspace.user_id == current_user.id,
        FileWorkspace.filename == file.filename
    ).first()

    if existing:
        # Delete old vector chunks if unstructured
        if existing.file_type in ["pdf", "text"]:
            from models.vector_store import DocumentChunk
            db.query(DocumentChunk).filter(DocumentChunk.workspace_id == existing.id).delete()
            db.commit()
        workspace = existing
    else:
        workspace = FileWorkspace(
            user_id=current_user.id,
            filename=file.filename,
            file_type=file_type,
            file_path=file_path
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    # Process based on file type
    if file_type == "excel":
        schema = extract_excel_schema(file_path)
        workspace.schema_json = schema
        db.commit()
        load_excel_to_postgres(file_path, workspace, db)
    elif file_type == "csv":
        schema = extract_csv_schema(file_path)
        workspace.schema_json = schema
        db.commit()
        load_excel_to_postgres(file_path, workspace, db)
    elif file_type == "pdf":
        process_pdf(file_path, workspace.id, db)
    elif file_type == "text":
        process_text_file(file_path, workspace.id, db)

    db.refresh(workspace)
    return {
        "workspace_id": workspace.id,
        "filename": workspace.filename,
        "file_type": workspace.file_type,
        "schema": workspace.schema_json
    }

@router.get("/list")
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspaces = db.query(FileWorkspace).filter(
        FileWorkspace.user_id == current_user.id
    ).order_by(FileWorkspace.updated_at.desc()).all()

    return [
        {
            "workspace_id": ws.id,
            "filename": ws.filename,
            "file_type": ws.file_type,
            "created_at": ws.created_at.isoformat(),
            "schema": ws.schema_json
        }
        for ws in workspaces
    ]
