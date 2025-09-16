#!/usr/bin/env python3
from __future__ import annotations
import argparse
from src.research_agent.agent import collect, score_and_save

def parse_args():
    p = argparse.ArgumentParser(
        description="Scholarly agent: arXiv / Crossref / PubMed / HAL / DBLP (+optional OpenAlex, DOAJ, CORE, Scopus/IEEE), per-paper JSON + BibTeX/CSL."
    )
    p.add_argument("topic", help="Research topic / query seed (in quotes)")
    p.add_argument("--years", default=None, help="YYYY or YYYY-YYYY (inclusive)")
    p.add_argument("--per-source", type=int, default=50, help="Max results per source")
    p.add_argument("--outdir", default="results", help="Output directory")

    # Scoring (LLM is now OPT-IN; pass a model name to enable)
    p.add_argument("--ollama-model", default="", help="Local LLM for re-ranking (e.g., 'llama3.1:8b'). Empty disables.")
    p.add_argument("--min-score", type=float, default=0.0, help="Drop papers below this score [0..1]")
    p.add_argument("--max-papers", type=int, default=None, help="Cap results after scoring")

    # Sources (free/open; OpenAlex optional; DOAJ/CORE default OFF for now)
    p.add_argument("--no-openalex", action="store_true", help="Disable OpenAlex")
    p.add_argument("--no-arxiv", action="store_true", help="Disable arXiv")
    p.add_argument("--crossref", action="store_true", help="Include Crossref")
    p.add_argument("--no-pubmed", action="store_true", help="Disable PubMed")
    p.add_argument("--no-hal", action="store_true", help="Disable HAL")
    p.add_argument("--no-dblp", action="store_true", help="Disable DBLP")
    p.add_argument("--use-doaj", action="store_true", help="Enable DOAJ (experimental)")
    p.add_argument("--use-core", action="store_true", help="Enable CORE (experimental)")

    # Paid APIs (opt-in; require env keys)
    p.add_argument("--use-scopus", action="store_true", help="Enable Scopus (requires SCOPUS_API_KEY)")
    p.add_argument("--use-ieee", action="store_true", help="Enable IEEE Xplore (requires IEEE_API_KEY)")

    # UX
    p.add_argument("--verbose", action="store_true", help="Print progress during collection and saving")
    p.add_argument("--incremental", action="store_true", help="Write files as we go (draft index)")

    return p.parse_args()

def main():
    args = parse_args()

    if args.verbose:
        print("[info] Collecting…")

    items = collect(
        topic=args.topic,
        years=args.years,
        per_source=args.per_source,
        use_openalex=not args.no_openalex,
        use_arxiv=not args.no_arxiv,
        use_crossref=args.crossref,
        use_pubmed=not args.no_pubmed,
        use_hal=not args.no_hal,
        use_dblp=not args.no_dblp,
        use_doaj=args.use_doaj,      # off unless passed
        use_core=args.use_core,      # off unless passed
        use_scopus=args.use_scopus,
        use_ieee=args.use_ieee,
        verbose=args.verbose,
    )
    if not items:
        print("[info] No results found.")
        return 0

    if args.verbose:
        print(f"[info] Collected {len(items)} unique items. Scoring and saving…")

    outbase, saved = score_and_save(
        topic=args.topic,
        items=items,
        outdir=args.outdir,
        ollama_model=(args.ollama_model or None),
        min_score=args.min_score,
        max_papers=args.max_papers,
        verbose=args.verbose,
        incremental=args.incremental,
        export_bibtex=True,
        export_csl=True,
    )
    print(f"[ok] Saved {saved} item(s) -> {outbase}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
