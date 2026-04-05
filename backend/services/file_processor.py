import copy
import os
import re
import pandas as pd
import pdfplumber
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from models.file_workspace import FileWorkspace
from services.schema_extractor import extract_excel_schema, extract_csv_schema
from services.embedding_service import get_embeddings_batch
from models.vector_store import DocumentChunk
from config import settings

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# ─── Data cleaning (ported from previous project's DatasetManager) ────

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean data values so they can be stored as proper numeric types.

    Handles:
      "$6,000"  → 6000.0  (currency)
      "50%"     → 50.0    (percentage)
      "1,234"   → 1234.0  (comma-separated numbers)
    """
    df = df.copy()

    for col in df.columns:
        if df[col].dtype != object:
            continue  # Only clean string columns

        sample = df[col].dropna().head(50)
        if len(sample) == 0:
            continue

        currency_pattern = re.compile(r'^\s*\$?[\d,]+\.?\d*\s*$')
        percent_pattern = re.compile(r'^\s*[\d,]+\.?\d*\s*%\s*$')

        currency_count = sample.apply(
            lambda x: bool(currency_pattern.match(str(x)))
        ).sum()
        percent_count = sample.apply(
            lambda x: bool(percent_pattern.match(str(x)))
        ).sum()

        threshold = len(sample) * 0.6  # 60% must match

        if percent_count >= threshold:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace('%', '', regex=False)
                .str.replace(',', '', regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

        elif currency_count >= threshold:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace('$', '', regex=False)
                .str.replace(',', '', regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


# ─── Helpers ──────────────────────────────────────────────────────────

def sanitize_table_name(user_id: int, filename: str, sheet_name: str) -> str:
    base = re.sub(r'[^a-z0-9]', '_', f"u{user_id}_{filename}_{sheet_name}".lower())
    return base[:60]


# ─── Excel / CSV → PostgreSQL ─────────────────────────────────────────

def load_excel_to_postgres(file_path: str, workspace: FileWorkspace, db: Session):
    """Load each Excel sheet (or CSV) into a separate PostgreSQL table."""
    schema = workspace.schema_json
    wb_sheets = schema.get("sheets", [])

    for sheet_info in wb_sheets:
        sheet_name = sheet_info["sheet_name"]
        table_name = sanitize_table_name(workspace.user_id, workspace.filename, sheet_name)

        # Read data — use header_row if available (Excel), default 0 (CSV)
        header_row = sheet_info.get("header_row", 0)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)

        df.dropna(how="all", inplace=True)

        # Clean data: strip $, %, commas from numeric-looking columns
        df = _clean_dataframe(df)

        # Clean column names for SQL and build mapping from original → sanitized
        original_cols = list(df.columns)
        sanitized_cols = [re.sub(r'[^a-z0-9]', '_', col.lower().strip()) for col in df.columns]
        df.columns = sanitized_cols

        # Drop and recreate table
        with db.get_bind().connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.commit()

        df.to_sql(table_name, db.get_bind(), if_exists="replace", index=False)
        sheet_info["table_name"] = table_name

        # Update schema column names to match the sanitized PostgreSQL column names
        col_name_map = {str(orig): san for orig, san in zip(original_cols, sanitized_cols)}
        for col_info in sheet_info.get("columns", []):
            original_name = col_info["name"]
            if original_name in col_name_map:
                col_info["original_name"] = original_name
                col_info["name"] = col_name_map[original_name]

    # Update workspace with table names — deep copy to force SQLAlchemy change detection
    workspace.schema_json = copy.deepcopy(schema)
    flag_modified(workspace, "schema_json")
    workspace.table_name = wb_sheets[0]["table_name"] if wb_sheets else None
    db.commit()


# ─── PDF / Text → Vector Store ────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """
    Split text into overlapping chunks using characters, identical to pgrag-main.
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
        
        start += chunk_size - overlap
    
    return chunks


def process_pdf(file_path: str, workspace_id: int, db: Session):
    """Extract text from PDF, chunk it, embed and store in vector DB."""
    full_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

    chunks = chunk_text(full_text)
    embeddings = get_embeddings_batch(chunks)

    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc = DocumentChunk(
            workspace_id=workspace_id,
            chunk_text=chunk,
            chunk_index=idx,
            embedding=embedding
        )
        db.add(doc)

    db.commit()


def process_text_file(file_path: str, workspace_id: int, db: Session):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    chunks = chunk_text(content)
    embeddings = get_embeddings_batch(chunks)

    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc = DocumentChunk(
            workspace_id=workspace_id,
            chunk_text=chunk,
            chunk_index=idx,
            embedding=embedding
        )
        db.add(doc)

    db.commit()
