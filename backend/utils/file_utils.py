import os
import re

def sanitize_filename(filename: str) -> str:
    """Remove or replace characters that are invalid in filenames."""
    return re.sub(r'[^\w\-_\. ]', '_', filename)

def ensure_dir(path: str):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
