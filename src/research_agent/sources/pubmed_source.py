# PubMed source via NCBI E-utilities (no key required).
# Optional: set PUBMED_EMAIL to identify yourself politely.
from __future__ import annotations
from typing import List, Dict
import os, time, requests

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

def _req(url: str, params: dict, retries: int = 4) -> requests.Response:
    ua = "research-agent/0.4 (PubMed)"
    headers = {"User-Agent": ua}
    delay = 0.8
    for _ in range(retries):
        r = requests.get(url, params=params, headers=headers, timeout=40)
        if r.status_code < 400:
            return r
        time.sleep(delay)
        delay = min(delay * 2, 6.0)
    r.raise_for_status()
    return r

def _year_from(pubdate: str | None) -> int | None:
    if not pubdate:
        return None
    # pubdate examples: "2024 Jan 12", "2022", "2023 Aug"
    try:
        return int(pubdate[:4])
    except Exception:
        return None

def search_pubmed(query: str, max_results: int = 50,
                  year_from: int | None = None, year_to: int | None = None) -> List[Dict]:
    email = os.getenv("PUBMED_EMAIL", "").strip()

    # 1) esearch: get list of PMIDs
    term = query
    if year_from or year_to:
        # PubMed date range with [dp] (date of publication)
        y1 = year_from or "1900"
        y2 = year_to or "3000"
        term = f"({query}) AND ({y1}[dp] : {y2}[dp])"
    params = {
        "db": "pubmed",
        "retmode": "json",
        "retmax": max_results,
        "term": term,
    }
    if email:
        params["email"] = email

    r = _req(ESEARCH, params)
    data = r.json()
    idlist = (data.get("esearchresult") or {}).get("idlist", [])
    if not idlist:
        return []

    # 2) esummary: fetch metadata for those PMIDs
    params = {
        "db": "pubmed",
        "retmode": "json",
        "id": ",".join(idlist),
    }
    if email:
        params["email"] = email
    r2 = _req(ESUMMARY, params)
    sdata = r2.json()

    result: List[Dict] = []
    uid_dict = (sdata.get("result") or {})
    for pmid in idlist:
        it = uid_dict.get(pmid) or {}
        title = (it.get("title") or "").strip(". ")
        # Authors: list of dicts {name: "Last F", authtype: "Author", ...}
        authors = [{"name": a.get("name", "")} for a in (it.get("authors") or []) if a.get("name")]
        pubdate = it.get("pubdate") or ""
        year = _year_from(pubdate)
        doi = ""
        for aid in it.get("articleids", []) or []:
            if aid.get("idtype") == "doi":
                doi = aid.get("value") or ""
                break
        url_page = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        # PubMed summaries sometimes include a "sortfirstauthor" and a "source"; abstract not in esummary typically.
        # We'll put abstract empty here (we rely on title & Crossref/arXiv/OpenAlex for abstracts).
        result.append({
            "title": title,
            "abstract": "",  # can be enriched by other sources later
            "year": year,
            "venue": it.get("source"),
            "doi": doi or None,
            "pubmed_id": pmid,
            "url_pdf": "",     # PubMed doesn't host PDFs; publisher page usually holds it
            "url_page": url_page,
            "authors": authors,
            "source": "pubmed",
            "source_payload": it,
        })
    return result
