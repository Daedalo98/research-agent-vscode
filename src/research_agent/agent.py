from __future__ import annotations
import os, json, sys
from typing import List, Dict, Tuple
from .utils import slugify, safe_hash, ensure_dir, write_json, simple_content_score, OllamaClient

# Sources
from .sources.openalex_source import search_openalex
from .sources.arxiv_source import search_arxiv
from .sources.crossref_source import search_crossref
from .sources.pubmed_source import search_pubmed
from .sources.hal_source import search_hal
from .sources.dblp_source import search_dblp
# optional/experimental
try:
    from .sources.doaj_source import search_doaj
except Exception:
    search_doaj = None  # type: ignore
try:
    from .sources.core_source import search_core
except Exception:
    search_core = None  # type: ignore
# paid
try:
    from .sources.scopus_source import search_scopus
except Exception:
    search_scopus = None  # type: ignore
try:
    from .sources.ieee_source import search_ieee
except Exception:
    search_ieee = None  # type: ignore

def _normalize_authors(auth_list):
    names = []
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
            ).strip()
        else:
            name = str(a).strip()
        if name:
            names.append(name)
    return names

def _dedup_key(item: Dict) -> str:
    for k in ("doi","arxiv_id","openalex_id","pubmed_id","hal_docid"):
        v = item.get(k)
        if v: return k + ":" + str(v).lower()
    title = (item.get("title") or "").lower()
    return "title:" + title[:160]

def collect(topic: str, years: str | None, per_source: int,
            *, use_openalex: bool = True, use_arxiv: bool = True, use_crossref: bool = False,
            use_pubmed: bool = True, use_hal: bool = True, use_dblp: bool = True,
            use_doaj: bool = False, use_core: bool = False,
            use_scopus: bool = False, use_ieee: bool = False,
            verbose: bool = False) -> List[Dict]:
    # parse years
    y1 = y2 = None
    if years:
        parts = years.split("-")
        if len(parts)==2:
            y1 = int(parts[0]) if parts[0] else None
            y2 = int(parts[1]) if parts[1] else None
        else:
            y1 = y2 = int(years)

    results: List[Dict] = []

    if use_openalex:
        try:
            if verbose: print("[info] Querying OpenAlex…", flush=True)
            results += search_openalex(topic, per_source, y1, y2)
        except Exception as e:
            print(f"[warn] OpenAlex error: {e}", file=sys.stderr)

    if use_arxiv:
        try:
            if verbose: print("[info] Querying arXiv…", flush=True)
            before = len(results)
            results += search_arxiv(topic, per_source, y1, y2)
            if verbose: print(f"[info] arXiv returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] arXiv error: {e}", file=sys.stderr)

    if use_pubmed:
        try:
            if verbose: print("[info] Querying PubMed…", flush=True)
            before = len(results)
            results += search_pubmed(topic, per_source, y1, y2)
            if verbose: print(f"[info] PubMed returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] PubMed error: {e}", file=sys.stderr)

    if use_hal:
        try:
            if verbose: print("[info] Querying HAL…", flush=True)
            before = len(results)
            results += search_hal(topic, per_source, y1, y2)
            if verbose: print(f"[info] HAL returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] HAL error: {e}", file=sys.stderr)

    if use_dblp:
        try:
            if verbose: print("[info] Querying DBLP…", flush=True)
            before = len(results)
            results += search_dblp(topic, per_source, y1, y2)
            if verbose: print(f"[info] DBLP returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] DBLP error: {e}", file=sys.stderr)

    if use_doaj and search_doaj:
        try:
            if verbose: print("[info] Querying DOAJ…", flush=True)
            before = len(results)
            results += search_doaj(topic, per_source, y1, y2)
            if verbose: print(f"[info] DOAJ returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] DOAJ error: {e}", file=sys.stderr)

    if use_core and search_core:
        try:
            if verbose: print("[info] Querying CORE…", flush=True)
            before = len(results)
            results += search_core(topic, per_source, y1, y2)
            if verbose: print(f"[info] CORE returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] CORE error: {e}", file=sys.stderr)

    if use_scopus and search_scopus:
        try:
            if verbose: print("[info] Querying Scopus…", flush=True)
            before = len(results)
            results += search_scopus(topic, per_source, y1, y2)
            if verbose: print(f"[info] Scopus returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] Scopus error: {e}", file=sys.stderr)

    if use_ieee and search_ieee:
        try:
            if verbose: print("[info] Querying IEEE Xplore…", flush=True)
            before = len(results)
            results += search_ieee(topic, per_source, y1, y2)
            if verbose: print(f"[info] IEEE returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] IEEE Xplore error: {e}", file=sys.stderr)

    if use_crossref:
        try:
            if verbose: print("[info] Querying Crossref…", flush=True)
            before = len(results)
            results += search_crossref(topic, per_source, y1, y2)
            if verbose: print(f"[info] Crossref returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] Crossref error: {e}", file=sys.stderr)

    # normalize authors
    for r in results:
        r["authors"] = _normalize_authors(r.get("authors"))

    # deduplicate
    seen, unique = set(), []
    for r in results:
        key = _dedup_key(r)
        if key in seen: 
            continue
        seen.add(key); unique.append(r)

    if verbose: print(f"[info] Unique after dedup: {len(unique)}", flush=True)
    return unique

def score_and_save(topic: str, items: List[Dict], outdir: str, ollama_model: str | None,
                   min_score: float = 0.0, max_papers: int | None = None,
                   verbose: bool = False, incremental: bool = False,
                   export_bibtex: bool = False, export_csl: bool = False) -> Tuple[str, int]:
    from .exporters import write_bibtex, write_csl_json

    topic_slug = slugify(topic)
    base = os.path.join(outdir, topic_slug)
    papers_dir = os.path.join(base, "papers")
    ensure_dir(papers_dir)

    draft_index = os.path.join(base, "index_draft.jsonl")
    final_index = os.path.join(base, "index.jsonl")
    if incremental:
        with open(draft_index, "w", encoding="utf-8") as _:
            pass

    llm = OllamaClient(model=ollama_model) if ollama_model else None
    if verbose:
        print(f"[info] Ollama {'enabled' if llm else 'disabled'}", flush=True)

    scored = []
    saved = 0
    for i, it in enumerate(items, 1):
        abstract = it.get("abstract") or ""
        title = it.get("title") or ""
        s_base = simple_content_score(topic, abstract or title)
        s_llm = llm.classify_relevance(topic, abstract) if (llm and abstract) else 0.0
        it["score"] = max(s_base, s_llm)
        scored.append(it)

        if verbose and (i % 5 == 0 or i == len(items)):
            print(f"[info] Scored {i}/{len(items)}…", flush=True)

        if incremental and it["score"] >= min_score:
            anchor = it.get("doi") or it.get("arxiv_id") or it.get("openalex_id") or it.get("pubmed_id") or it.get("hal_docid") or it.get("title","")
            name = safe_hash(str(anchor))
            write_json(os.path.join(papers_dir, f"{name}.json"), it)
            with open(draft_index, "a", encoding="utf-8") as idx:
                idx.write(json.dumps({
                    "id": name,
                    "title": it.get("title",""),
                    "year": it.get("year"),
                    "doi": it.get("doi"),
                    "arxiv_id": it.get("arxiv_id"),
                    "openalex_id": it.get("openalex_id"),
                    "pubmed_id": it.get("pubmed_id"),
                    "hal_docid": it.get("hal_docid"),
                    "score": it.get("score",0.0),
                    "source": it.get("source",""),
                    "url_page": it.get("url_page",""),
                    "url_pdf": it.get("url_pdf",""),
                }, ensure_ascii=False) + "\n")
            saved += 1
            if verbose and (saved % 5 == 0):
                print(f"[info] Incrementally saved {saved} items…", flush=True)

    # final pass & index
    filtered = [it for it in scored if it["score"] >= min_score]
    filtered.sort(key=lambda x: (x.get("score",0), x.get("year") or 0), reverse=True)
    if max_papers is not None:
        filtered = filtered[:max_papers]

    with open(final_index, "w", encoding="utf-8") as idx:
        for it in filtered:
            anchor = it.get("doi") or it.get("arxiv_id") or it.get("openalex_id") or it.get("pubmed_id") or it.get("hal_docid") or it.get("title","")
            name = safe_hash(str(anchor))
            write_json(os.path.join(papers_dir, f"{name}.json"), it)
            idx.write(json.dumps({
                "id": name,
                "title": it.get("title",""),
                "year": it.get("year"),
                "doi": it.get("doi"),
                "arxiv_id": it.get("arxiv_id"),
                "openalex_id": it.get("openalex_id"),
                "pubmed_id": it.get("pubmed_id"),
                "hal_docid": it.get("hal_docid"),
                "score": it.get("score",0.0),
                "source": it.get("source",""),
                "url_page": it.get("url_page",""),
                "url_pdf": it.get("url_pdf",""),
            }, ensure_ascii=False) + "\n")

    if export_bibtex:
        write_bibtex(os.path.join(base, "export.bib"), filtered)
        if verbose: print("[info] Wrote BibTeX: export.bib", flush=True)
    if export_csl:
        write_csl_json(os.path.join(base, "export.csl.json"), filtered)
        if verbose: print("[info] Wrote CSL-JSON: export.csl.json", flush=True)

    return base, len(filtered)
