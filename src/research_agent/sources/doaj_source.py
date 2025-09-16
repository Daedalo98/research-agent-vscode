from __future__ import annotations
from typing import List, Dict
import requests

DOAJ_API = "https://doaj.org/api/v2/search/articles/"

def search_doaj(query: str, max_results: int = 50,
                year_from: int | None = None,
                year_to: int | None = None) -> List[Dict]:
    """
    Search DOAJ (Directory of Open Access Journals).
    API docs: https://doaj.org/api/v2/docs
    """
    params = {"q": query, "pageSize": max_results}
    r = requests.get(DOAJ_API, params=params, timeout=40)
    r.raise_for_status()
    data = r.json()

    out: List[Dict] = []
    for it in data.get("results", []):
        bib = it.get("bibjson", {})
        year = int(bib.get("year")) if bib.get("year") else None
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        authors = [{"name": a.get("name")} for a in bib.get("author", [])]
        out.append({
            "title": bib.get("title", ""),
            "abstract": bib.get("abstract", ""),
            "year": year,
            "doi": bib.get("identifier", [{}])[0].get("id"),
            "url_page": bib.get("link", [{}])[0].get("url"),
            "url_pdf": "",
            "authors": authors,
            "venue": (bib.get("journal", {}) or {}).get("title"),
            "source": "doaj",
            "source_payload": it,
        })
    return out
