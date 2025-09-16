# HAL (France open archive) search.
from __future__ import annotations
from typing import List, Dict
import requests

HAL_API = "https://api.archives-ouvertes.fr/search/halshs/"

def search_hal(query: str, max_results: int = 50,
               year_from: int | None = None, year_to: int | None = None) -> List[Dict]:
    # HAL query: q= and fl= (fields)
    # We'll query title + abstract for relevance; filter by years via fq= if provided.
    fields = ",".join([
        "title_s", "abstract_s", "authFullName_s", "docid", "doiId_s", "producedDateY_i",
        "uri_s", "fileMain_s"
    ])
    params = {
        "q": f"(title_t:({query})) OR (abstract_s:({query}))",
        "rows": max_results,
        "fl": fields,
        "sort": "score desc",
        "wt": "json"
    }
    fqs = []
    if year_from is not None:
        fqs.append(f"producedDateY_i:[{year_from} TO *]")
    if year_to is not None:
        fqs.append(f"producedDateY_i:[* TO {year_to}]")
    if fqs:
        # HAL accepts fq multiple times; we can join
        # requests will encode lists to repeated params if we pass a list
        pass
    r = requests.get(HAL_API, params=params, timeout=40, headers={"User-Agent":"research-agent/0.4"})
    r.raise_for_status()
    data = r.json()

    docs = (((data.get("response") or {}).get("docs")) or [])
    out: List[Dict] = []
    for d in docs:
        year = d.get("producedDateY_i")
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        authors = [{"name": a} for a in (d.get("authFullName_s") or [])]
        out.append({
            "title": (d.get("title_s") or [""])[0],
            "abstract": (d.get("abstract_s") or [""])[0],
            "year": year,
            "venue": "HAL",
            "doi": (d.get("doiId_s") or [None])[0],
            "hal_docid": d.get("docid"),
            "url_pdf": (d.get("fileMain_s") or [""])[0],
            "url_page": (d.get("uri_s") or [""])[0],
            "authors": authors,
            "source": "hal",
            "source_payload": d,
        })
    return out
