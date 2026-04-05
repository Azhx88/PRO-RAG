import google.generativeai as genai
from config import settings
import time

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)

class RateLimiter:
    """
    Rate limiter for Gemini free tier (15 RPM).
    Uses 12 RPM to provide safety buffer.
    Synchronous implementation based on pgrag-main.
    """
    def __init__(self, max_calls: int = 12, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls: list[datetime] = []
    
    def wait_if_needed(self):
        now = datetime.now()
        # Remove calls older than the time window
        self.calls = [
            call_time for call_time in self.calls 
            if now - call_time < timedelta(seconds=self.period)
        ]
        
        if len(self.calls) >= self.max_calls:
            oldest_call = min(self.calls)
            wait_time = (oldest_call + timedelta(seconds=self.period) - now).total_seconds()
            if wait_time > 0:
                logger.info(f"⏳ Rate limit: waiting {wait_time:.1f}s before next API call...")
                time.sleep(wait_time + 0.5)
        
        self.calls.append(now)

# Global rate limiter instance
_rate_limiter = RateLimiter(max_calls=12, period=60)

def get_embedding(text: str, task_type: str = "retrieval_document") -> list[float]:
    _rate_limiter.wait_if_needed()
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type=task_type
    )
    return result["embedding"][:768]

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in batches (20x more efficient).
    Supported seamlessly by Gemini payload.
    """
    if not texts:
        return []

    BATCH_SIZE = 100
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        _rate_limiter.wait_if_needed()
        logger.info(f"📊 Embedding batch {i//BATCH_SIZE + 1} ({len(batch)} chunks)...")

        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=batch,
            task_type="retrieval_document"
        )
        
        try:
            batch_embeddings = result['embedding'] 
            if isinstance(batch_embeddings[0], float):
                batch_embeddings = [batch_embeddings]
        except KeyError:
            batch_embeddings = [emb['values'] for emb in result.get('embeddings', [])]
            
        all_embeddings.extend([emb[:768] for emb in batch_embeddings])
        
    logger.info(f"✅ Generated {len(all_embeddings)} embeddings total")
    return all_embeddings
