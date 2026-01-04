"""URL utilities."""
from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.lower().strip())
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"
