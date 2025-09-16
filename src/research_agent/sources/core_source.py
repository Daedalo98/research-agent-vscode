from __future__ import annotations
from typing import List, Dict
import requests

CORE_API = "https://core.ac.uk:443/api-v3/search/works"

def search_core(query: str, max_results: int = 50,
                year_from: int | None = None,
                year_to: int | None = None) -> List[Dict]:
    """
    Search CORE (global open access aggregator).
    API docs: https://core.ac.uk/services#api
    """
    params = {"q": query, "limit": max_results}
    r = requests.get(CORE_API, params=params, timeout=40)
    r.raise_for_status()
    data = r.json()

    out: List[Dict] = []
    for it in data.get("results", []):
        meta = it.get("metadata", {})
        year = int(meta.get("publishedDate", "")[:4]) if meta.get("publishedDate") else None
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        authors = [{"name": a} for a in (meta.get("authors") or [])]
        out.append({
            "title": meta.get("title", ""),
            "abstract": meta.get("description", ""),
            "year": year,
            "doi": meta.get("doi"),
            "url_page": meta.get("urls", [None])[0],
            "url_pdf": "",
            "authors": authors,
            "venue": meta.get("publisher"),
            "source": "core",
            "source_payload": it,
        })
    return out
