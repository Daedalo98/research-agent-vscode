from __future__ import annotations
from typing import Dict, List
import re, json, hashlib

# ---------- Helpers ----------
def _tex_escape(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\\", "\\\\")
    s = s.replace("{", "\\{").replace("}", "\\}")
    s = s.replace("&", "\\&").replace("%", "\\%").replace("$", "\\$")
    s = s.replace("#", "\\#").replace("_", "\\_").replace("^", "\\^{}").replace("~", "\\~{}")
    return s

def _as_author_strings(auth_list) -> List[str]:
    """
    Coerce a heterogeneous author list (str or dict) into a list[str] of names.
    Supports dict shapes like:
      {"name": "First Last"}
      {"full_name": "First Last"}
      {"display_name": "First Last"}
      {"text": "First Last"}               # DBLP
      {"given": "...", "family": "..."}    # CSL-ish
    """
    out: List[str] = []
    for a in (auth_list or []):
        if isinstance(a, str):
            name = a.strip()
        elif isinstance(a, dict):
            name = (
                a.get("name")
                or a.get("full_name")
                or a.get("display_name")
                or a.get("text")
                or (" ".join([x for x in [a.get("given"), a.get("family")] if x]))
                or ""
            )
            name = str(name).strip()
        else:
            name = str(a).strip()
        if name:
            out.append(name)
    return out

def _key_from(item: Dict) -> str:
    base = (
        item.get("doi")
        or item.get("arxiv_id")
        or item.get("pubmed_id")
        or item.get("openalex_id")
        or item.get("hal_docid")
        or item.get("title", "")
    )
    h = hashlib.sha1(str(base).encode("utf-8")).hexdigest()[:8]
    # lastname + year + short hash
    authors = _as_author_strings(item.get("authors"))
    last = ""
    if authors:
        last = re.sub(r"[^a-zA-Z]", "", authors[0].split()[-1]).lower()
    year = str(item.get("year") or "")
    return f"{last}{year}{h}"

# ---------- BibTeX ----------
def to_bibtex_entries(items: List[Dict]) -> str:
    lines: List[str] = []
    for it in items:
        entry_type = "article"
        key = _key_from(it)
        title = _tex_escape(it.get("title", ""))
        year = it.get("year")
        doi = it.get("doi") or ""
        venue = it.get("venue") or ""
        url = it.get("url_page") or it.get("url_pdf") or ""

        authors = _as_author_strings(it.get("authors"))
        authors_field = " and ".join(_tex_escape(a) for a in authors)

        lines.append(f"@{entry_type}{{{key},")
        if title:   lines.append(f"  title = {{{title}}},")
        if authors_field: lines.append(f"  author = {{{authors_field}}},")
        if venue:   lines.append(f"  journal = {{{_tex_escape(venue)}}},")
        if year:    lines.append(f"  year = {{{year}}},")
        if doi:     lines.append(f"  doi = {{{doi}}},")
        if url:     lines.append(f"  url = {{{_tex_escape(url)}}},")
        lines.append("}\n")
    return "\n".join(lines)

# ---------- CSL-JSON ----------
def to_csl_json_list(items: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for it in items:
        author_names = _as_author_strings(it.get("authors"))
        authors = []
        for a in author_names:
            parts = a.split()
            if len(parts) >= 2:
                given = " ".join(parts[:-1])
                family = parts[-1]
            else:
                given, family = a, ""
            authors.append({"given": given, "family": family})

        ent = {
            "type": "article-journal",
            "title": it.get("title", ""),
            "author": authors,
            "issued": {"date-parts": [[it.get("year")]]} if it.get("year") else None,
            "DOI": it.get("doi") or None,
            "URL": it.get("url_page") or it.get("url_pdf") or None,
            "container-title": it.get("venue") or None,
            "id": _key_from(it),
        }
        # remove Nones
        ent = {k: v for k, v in ent.items() if v not in (None, "", [])}
        out.append(ent)
    return out

def write_bibtex(path: str, items: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_bibtex_entries(items))

def write_csl_json(path: str, items: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_csl_json_list(items), f, ensure_ascii=False, indent=2)
