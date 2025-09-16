from __future__ import annotations
from typing import List, Dict
import os, requests

IEEE_API = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

def search_ieee(query: str, max_results: int = 50,
                year_from: int | None = None,
                year_to: int | None = None) -> List[Dict]:
    """
    IEEE Xplore search.
    Requires: export IEEE_API_KEY=your_key
    Docs: https://developer.ieee.org/
    """
    key = os.getenv("IEEE_API_KEY")
    if not key:
        raise RuntimeError("IEEE_API_KEY not set")

    params = {"apikey": key, "querytext": query, "max_records": max_results, "format": "json"}
    r = requests.get(IEEE_API, params=params, timeout=40)
    r.raise_for_status()
    data = r.json()

    out: List[Dict] = []
    for it in data.get("articles", []):
        year = int(it.get("publication_year")) if it.get("publication_year") else None
        out.append({
            "title": it.get("title", ""),
            "abstract": it.get("abstract", ""),
            "year": year,
            "doi": it.get("doi"),
            "url_page": it.get("html_url"),
            "url_pdf": it.get("pdf_url"),
            "authors": [{"name": a.get("full_name")} for a in (it.get("authors", {}).get("authors", []) or [])],
            "venue": it.get("publication_title"),
            "source": "ieee",
            "source_payload": it,
        })
    return out
