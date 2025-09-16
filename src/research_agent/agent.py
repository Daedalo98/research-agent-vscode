from __future__ import annotations
import os, json, sys
from typing import List, Dict, Tuple
from .utils import slugify, safe_hash, ensure_dir, write_json, simple_content_score, OllamaClient
from .sources.openalex_source import search_openalex
from .sources.arxiv_source import search_arxiv
from .sources.crossref_source import search_crossref

def _normalize_authors(auth_list):
    names = []
    for a in (auth_list or []):
        name = a.get("name") if isinstance(a, dict) else str(a)
        if name: names.append(name)
    return names

def _dedup_key(item: Dict) -> str:
    for k in ("doi","arxiv_id","openalex_id"):
        v = item.get(k)
        if v: return k + ":" + str(v).lower()
    title = (item.get("title") or "").lower()
    return "title:" + title[:160]

def collect(topic: str, years: str | None, per_source: int,
            use_openalex: bool = True, use_arxiv: bool = True, use_crossref: bool = False,
            verbose: bool = False) -> List[Dict]:
    """Fetch results from enabled sources, then deduplicate."""
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
            if verbose: print(f"[info] OpenAlex returned {len(results)} total so far.", flush=True)
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

    if use_crossref:
        try:
            if verbose: print("[info] Querying Crossref…", flush=True)
            before = len(results)
            results += search_crossref(topic, per_source, y1, y2)
            if verbose: print(f"[info] Crossref returned {len(results)-before} items.", flush=True)
        except Exception as e:
            print(f"[warn] Crossref error: {e}", file=sys.stderr)

    for r in results:
        r["authors"] = _normalize_authors(r.get("authors"))

    # Deduplicate
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
                   verbose: bool = False, incremental: bool = False) -> Tuple[str, int]:
    """
    If incremental=True:
      - create results dirs up-front
      - write index_draft.jsonl as we accept items
      - write each per-paper JSON as soon as it's scored & passes the filter
    Returns (base_output_path, saved_count)
    """
    topic_slug = slugify(topic)
    base = os.path.join(outdir, topic_slug)
    papers_dir = os.path.join(base, "papers")
    ensure_dir(papers_dir)

    draft_index = os.path.join(base, "index_draft.jsonl")
    final_index = os.path.join(base, "index.jsonl")
    if incremental:
        # start a fresh draft
        with open(draft_index, "w", encoding="utf-8") as _:
            pass

    # Prepare LLM (optional)
    llm = OllamaClient(model=ollama_model) if ollama_model else None
    if verbose:
        if llm:
            print(f"[info] Using Ollama model: {ollama_model}", flush=True)
        else:
            print("[info] Ollama disabled (no model specified).", flush=True)

    # Score + optionally save incrementally
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
            # write per-paper file now
            anchor = it.get("doi") or it.get("arxiv_id") or it.get("openalex_id") or it.get("title","")
            name = safe_hash(str(anchor))
            path = os.path.join(papers_dir, f"{name}.json")
            write_json(path, it)
            # append to draft index
            with open(draft_index, "a", encoding="utf-8") as idx:
                idx.write(json.dumps({
                    "id": name,
                    "title": it.get("title",""),
                    "year": it.get("year"),
                    "doi": it.get("doi"),
                    "arxiv_id": it.get("arxiv_id"),
                    "openalex_id": it.get("openalex_id"),
                    "score": it.get("score",0.0),
                    "source": it.get("source",""),
                    "url_page": it.get("url_page",""),
                    "url_pdf": it.get("url_pdf",""),
                }, ensure_ascii=False) + "\n")
            saved += 1
            if verbose and (saved % 5 == 0):
                print(f"[info] Incrementally saved {saved} items so far…", flush=True)

    # If not incremental, filter and write everything now
    if not incremental:
        scored = [it for it in scored if it["score"] >= min_score]
        scored.sort(key=lambda x: (x.get("score",0), x.get("year") or 0), reverse=True)
        if max_papers is not None:
            scored = scored[:max_papers]

        index_path = os.path.join(base, "index.jsonl")
        with open(index_path, "w", encoding="utf-8") as idx:
            for it in scored:
                anchor = it.get("doi") or it.get("arxiv_id") or it.get("openalex_id") or it.get("title","")
                name = safe_hash(str(anchor))
                path = os.path.join(papers_dir, f"{name}.json")
                write_json(path, it)
                idx.write(json.dumps({
                    "id": name,
                    "title": it.get("title",""),
                    "year": it.get("year"),
                    "doi": it.get("doi"),
                    "arxiv_id": it.get("arxiv_id"),
                    "openalex_id": it.get("openalex_id"),
                    "score": it.get("score",0.0),
                    "source": it.get("source",""),
                    "url_page": it.get("url_page",""),
                    "url_pdf": it.get("url_pdf",""),
                }, ensure_ascii=False) + "\n")
                saved += 1
        return base, saved

    # If incremental: we already wrote per-paper files on the fly.
    # We still produce a final, cleaned/sorted index.
    filtered = [it for it in scored if it["score"] >= min_score]
    filtered.sort(key=lambda x: (x.get("score",0), x.get("year") or 0), reverse=True)
    if max_papers is not None:
        filtered = filtered[:max_papers]

    with open(final_index, "w", encoding="utf-8") as idx:
        for it in filtered:
            anchor = it.get("doi") or it.get("arxiv_id") or it.get("openalex_id") or it.get("title","")
            name = safe_hash(str(anchor))
            idx.write(json.dumps({
                "id": name,
                "title": it.get("title",""),
                "year": it.get("year"),
                "doi": it.get("doi"),
                "arxiv_id": it.get("arxiv_id"),
                "openalex_id": it.get("openalex_id"),
                "score": it.get("score",0.0),
                "source": it.get("source",""),
                "url_page": it.get("url_page",""),
                "url_pdf": it.get("url_pdf",""),
            }, ensure_ascii=False) + "\n")

    if verbose:
        print(f"[info] Final index written: {final_index}", flush=True)
    return base, saved
