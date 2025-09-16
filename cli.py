#!/usr/bin/env python3
from __future__ import annotations
import argparse
from src.research_agent.agent import collect, score_and_save

def parse_args():
    p = argparse.ArgumentParser(description="Search OpenAlex + arXiv (optional Crossref) and export per-paper JSON.")
    p.add_argument("topic", help="Research topic / query seed (in quotes)")
    p.add_argument("--years", default=None, help="YYYY or YYYY-YYYY (inclusive)")
    p.add_argument("--per-source", type=int, default=50, help="Max results per source")
    p.add_argument("--outdir", default="results", help="Output directory")

    # Scoring (local model optional)
    p.add_argument("--ollama-model", default="llama3.1:8b", help="Local LLM for re-ranking (e.g., llama3.1:8b)")
    p.add_argument("--min-score", type=float, default=0.0, help="Drop papers below this score [0..1]")
    p.add_argument("--max-papers", type=int, default=None, help="Cap results after scoring")

    # Sources
    p.add_argument("--no-openalex", action="store_true", help="Disable OpenAlex")
    p.add_argument("--no-arxiv", action="store_true", help="Disable arXiv")
    p.add_argument("--crossref", action="store_true", help="Also search Crossref (for DOI coverage)")

    # NEW: verbosity
    p.add_argument("--verbose", action="store_true", help="Print progress during collection and saving")
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
        verbose=args.verbose,              # NEW
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
        ollama_model=args.ollama_model,
        min_score=args.min_score,
        max_papers=args.max_papers,
        verbose=args.verbose,              # NEW
        incremental=True,                  # NEW: write as we go
    )
    print(f"[ok] Saved {saved} item(s) -> {outbase}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
