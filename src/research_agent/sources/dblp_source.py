from __future__ import annotations
from typing import List, Dict, Union
import requests

DBLP_API = "https://dblp.org/search/publ/api"

def _authors_from_info(info: Dict) -> List[Dict[str, str]]:
    """
    DBLP 'author' can be:
      - a list of dicts: [{"text": "First Last"}, ...]
      - a single dict:   {"text": "First Last"}
      - a string (rare)
    We normalize to [{"name": "First Last"}, ...]
    """
    raw = (info.get("authors") or {}).get("author", [])
    if isinstance(raw, dict):  # single author case
        raw = [raw]
    authors: List[Dict[str, str]] = []
    for a in raw:
        if isinstance(a, dict):
            name = a.get("text") or a.get("name") or ""
        else:
            name = str(a)
        name = name.strip()
        if name:
            authors.append({"name": name})
    return authors

def search_dblp(query: str, max_results: int = 50,
                year_from: int | None = None,
                year_to: int | None = None) -> List[Dict]:
    """
    Search DBLP (computer science) publications.
    API: https://dblp.org/faq/13501473.html
    """
    params = {"q": query, "h": max_results, "format": "json"}
    r = requests.get(DBLP_API, params=params, timeout=40, headers={"User-Agent": "research-agent/0.4"})
    r.raise_for_status()
    data = r.json()

    out: List[Dict] = []
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    for h in hits:
        info = h.get("info", {})
        year = int(info.get("year")) if info.get("year") else None
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue

        authors = _authors_from_info(info)
        out.append({
            "title": info.get("title", ""),
            "abstract": "",  # DBLP does not expose abstracts
            "year": year,
            "doi": info.get("doi"),
            "url_page": info.get("url"),
            "url_pdf": "",
            "authors": authors,  # list[{"name": "..."}]
            "venue": info.get("venue"),
            "source": "dblp",
            "source_payload": info,
        })
    return out
