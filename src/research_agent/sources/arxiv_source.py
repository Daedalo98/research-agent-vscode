# arXiv source (Atom feed). We parse with the stdlib XML parser.
from __future__ import annotations
from typing import List, Dict
import requests, xml.etree.ElementTree as ET

ARXIV_API = "https://export.arxiv.org/api/query"

def _text(elem, tag, ns):
    node = elem.find(tag, ns)
    return (node.text or "").strip() if node is not None and node.text else ""

def search_arxiv(query: str, max_results: int = 50, year_from: int | None = None, year_to: int | None = None) -> List[Dict]:
    # Conservative AND between terms; you can improve this if needed.
    terms = " AND ".join([t for t in query.split() if t.strip()])
    params = {
        "search_query": f"all:{terms}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    r = requests.get(ARXIV_API, params=params, timeout=40, headers={"User-Agent":"research-agent/0.3"})
    r.raise_for_status()

    root = ET.fromstring(r.text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = []
    for entry in root.findall("a:entry", ns):
        title = _text(entry, "a:title", ns)
        summary = _text(entry, "a:summary", ns)
        page = _text(entry, "a:id", ns)
        published = _text(entry, "a:published", ns)
        year = None
        if published:
            try:
                year = int(published[:4])
            except Exception:
                pass

        # find a PDF link (if exposed)
        url_pdf = ""
        for link in entry.findall("a:link", ns):
            if link.get("title") == "pdf" and link.get("href"):
                url_pdf = link.get("href")
                break

        arxiv_id = page.rsplit("/",1)[-1] if page else ""

        if year_from and year and year < year_from: 
            continue
        if year_to and year and year > year_to: 
            continue

        authors = []
        for a in entry.findall("a:author", ns):
            nm = _text(a, "a:name", ns)
            if nm:
                authors.append({"name": nm})

        entries.append({
            "title": " ".join(title.split()),
            "abstract": " ".join(summary.split()),
            "year": year,
            "url_pdf": url_pdf,
            "url_page": page,
            "arxiv_id": arxiv_id,
            "doi": None,
            "venue": "arXiv",
            "authors": authors,
            "source": "arxiv",
            "source_payload": {},
        })
    return entries
