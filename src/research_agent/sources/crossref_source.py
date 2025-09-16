# Crossref (optional) — useful for finding DOIs and publisher landing pages.
from __future__ import annotations
from typing import List, Dict
import requests

CROSSREF_API = "https://api.crossref.org/works"

def search_crossref(query: str, max_results: int = 50,
                    year_from: int | None = None, year_to: int | None = None) -> List[Dict]:
    params = {
        "query": query,
        "rows": max_results,
        "select": ",".join(["title","author","issued","DOI","URL","type"]),
        "sort": "relevance",
        "filter": "type:journal-article",
    }
    filters = ["type:journal-article"]
    if year_from:
        filters.append(f"from-pub-date:{year_from}-01-01")
    if year_to:
        filters.append(f"until-pub-date:{year_to}-12-31")
    params["filter"] = ",".join(filters)

    r = requests.get(CROSSREF_API, params=params, timeout=40, headers={"User-Agent":"research-agent/0.3"})
    r.raise_for_status()
    data = r.json()
    out: List[Dict] = []
    for it in data.get("message", {}).get("items", []):
        if it.get("type") != "journal-article":
            continue
        title = "; ".join(it.get("title") or [])
        authors = [{"name": " ".join([a.get("given",""), a.get("family","")]).strip()}
                   for a in (it.get("author") or [])]
        # extract year if present
        year = None
        issued = it.get("issued") or {}
        parts = issued.get("date-parts") or []
        if parts and parts[0] and isinstance(parts[0][0], int):
            year = int(parts[0][0])
        out.append({
            "title": title,
            "abstract": "",
            "year": year,
            "venue": "",
            "doi": it.get("DOI"),
            "url_page": it.get("URL"),
            "url_pdf": "",
            "authors": authors,
            "source": "crossref",
            "source_payload": it,
        })
    return out
