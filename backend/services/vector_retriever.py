from sqlalchemy import text
from sqlalchemy.orm import Session
from services.embedding_service import get_embedding
from services.llm_service import call_groq

TOP_K = 5

def retrieve_chunks(query: str, workspace_id: int, db: Session) -> list[dict]:
    query_embedding = get_embedding(query, task_type="retrieval_query")
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    sql = text(f"""
        SELECT 
            dc.chunk_text,
            dc.chunk_index,
            fw.filename,
            1 - (dc.embedding <=> cast(:embedding AS vector)) AS similarity
        FROM document_chunks dc
        JOIN file_workspaces fw ON fw.id = dc.workspace_id
        WHERE dc.workspace_id = :workspace_id
        ORDER BY dc.embedding <=> cast(:embedding AS vector)
        LIMIT :top_k
    """)

    result = db.execute(sql, {
        "embedding": embedding_str,
        "workspace_id": workspace_id,
        "top_k": TOP_K
    })
    
    chunks = []
    for row in result.fetchall():
        chunks.append({
            "text": row[0],
            "index": row[1],
            "filename": row[2]
        })
    return chunks

def generate_rag_response(query: str, chunks: list[dict]) -> str:
    formatted_chunks = [
        f"[Source: {chunk['filename']}, chunk {chunk['index']}]\n{chunk['text']}"
        for chunk in chunks
    ]
    context = "\n\n---\n\n".join(formatted_chunks)
    
    prompt = f"""You are a helpful assistant. Answer the user's question using only the provided context.

CONTEXT:
{context}

QUESTION: {query}

If the answer is not in the context, say "I couldn't find that information in the document."
Answer:"""

    return call_groq(prompt, system="You are a helpful document QA assistant.")
