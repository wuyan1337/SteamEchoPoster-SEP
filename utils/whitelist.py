from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url
    p = urlsplit(url)
    scheme = (p.scheme or "https").lower()
    netloc = p.netloc.lower()
    path = p.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((scheme, netloc, path, "", ""))

def load_list(path: str | Path) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    items: set[str] = set()
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        items.add(normalize_url(s))
    return items
