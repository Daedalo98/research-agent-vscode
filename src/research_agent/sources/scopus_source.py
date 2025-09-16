from __future__ import annotations
from typing import List, Dict
import os, requests

SCOPUS_API = "https://api.elsevier.com/content/search/scopus"

def search_scopus(query: str, max_results: int = 50,
                  year_from: int | None = None,
                  year_to: int | None = None) -> List[Dict]:
    """
    Scopus search.
    Requires: export SCOPUS_API_KEY=your_key
    Docs: https://dev.elsevier.com/documentation/ScopusAPI.wadl
    """
    key = os.getenv("SCOPUS_API_KEY")
    if not key:
        raise RuntimeError("SCOPUS_API_KEY not set")

    headers = {"X-ELS-APIKey": key, "Accept": "application/json"}
    params = {"query": query, "count": max_results}
    r = requests.get(SCOPUS_API, params=params, headers=headers, timeout=40)
    r.raise_for_status()
    data = r.json()

    out: List[Dict] = []
    for e in data.get("search-results", {}).get("entry", []):
        year = int(e.get("prism:coverDate", "")[:4]) if e.get("prism:coverDate") else None
        out.append({
            "title": e.get("dc:title", ""),
            "abstract": e.get("dc:description", ""),
            "year": year,
            "doi": e.get("prism:doi"),
            "url_page": e.get("prism:url"),
            "url_pdf": "",
            "authors": [{"name": e.get("dc:creator")}],
            "venue": e.get("prism:publicationName"),
            "source": "scopus",
            "source_payload": e,
        })
    return out
