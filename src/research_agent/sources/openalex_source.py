# src/research_agent/sources/openalex_source.py
from __future__ import annotations
from typing import List, Dict, Optional
import os, time, requests

OPENALEX = "https://api.openalex.org/works"

def _reconstruct_abstract(inv_idx: Optional[dict]) -> str:
    if not inv_idx:
        return ""
    positions = []
    for word, idxs in inv_idx.items():
        for i in idxs:
            positions.append((i, word))
    if not positions:
        return ""
    positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in positions)

def _request_with_retries(params: dict, headers: dict, retries: int = 5) -> requests.Response:
    """
    Friendly backoff for 403/429/5xx. OpenAlex appreciates: mailto + good UA + not bursting.
    """
    delay = 1.0
    for attempt in range(1, retries + 1):
        r = requests.get(OPENALEX, params=params, headers=headers, timeout=40)
        if r.status_code < 400:
            return r
        if r.status_code in (403, 429) or 500 <= r.status_code < 600:
            # exponential backoff with jitter
            time.sleep(delay)
            delay = min(delay * 2.0, 16.0)
            continue
        # other client errors: raise immediately
        r.raise_for_status()
    # if we exhausted retries, raise last error
    r.raise_for_status()
    return r  # to satisfy type checker

def search_openalex(
    query: str,
    max_results: int = 50,
    year_from: int | None = None,
    year_to: int | None = None,
) -> List[Dict]:
    # Email helps OpenAlex contact if needed. Recommended.
    mailto = os.getenv("OPENALEX_MAILTO", "").strip()

    # Build filters the way OpenAlex likes them: a single "filter" param with CSV of constraints
    filters = []
    if year_from:
        filters.append(f"from_publication_date:{year_from}-01-01")
    if year_to:
        filters.append(f"to_publication_date:{year_to}-12-31")

    params = {
        # Full-text search across metadata
        "search": query,
        # Try modest page size while testing. You can raise later.
        "per_page": max(1, min(max_results, 200)),
        # Strongly relevant first
        "sort": "relevance_score:desc",
    }
    if filters:
        params["filter"] = ",".join(filters)
    if mailto:
        params["mailto"] = mailto

    headers = {
        # Strong UA with contact is recommended.
        "User-Agent": f"research-agent/0.4 (+https://example.org; mailto:{mailto or 'contact@example.org'})",
        "Accept": "application/json",
    }

    r = _request_with_retries(params, headers, retries=5)
    data = r.json()

    out: List[Dict] = []
    for w in data.get("results", []):
        title = w.get("title") or ""
        year = w.get("publication_year")
        doi = (w.get("ids") or {}).get("doi")
        url_page = (w.get("primary_location") or {}).get("landing_page_url") or (w.get("host_venue") or {}).get("url") or ""
        url_pdf = (w.get("primary_location") or {}).get("pdf_url") or ""
        authors = [{"name": a.get("author", {}).get("display_name","")} for a in (w.get("authorships") or [])]
        abstract = _reconstruct_abstract(w.get("abstract_inverted_index"))
        venue = (w.get("host_venue") or {}).get("display_name")

        out.append({
            "title": title,
            "abstract": abstract,
            "year": year,
            "venue": venue,
            "doi": doi,
            "openalex_id": w.get("id"),
            "url_pdf": url_pdf,
            "url_page": url_page,
            "authors": authors,
            "source": "openalex",
            "source_payload": w,
        })
    return out
