# Research Agent (VS Code) — OpenAlex + arXiv (free), per-paper JSON, optional local LLM reranking

This agent searches **OpenAlex** (free, no key) and **arXiv** (free) to collect papers about a topic,
then saves **one JSON per paper** plus an **index.jsonl**. It can re-rank by content relevance using your
**local Ollama** model (e.g., `llama3.1:8b`).

> Why free? We avoid paid APIs. For OpenAlex, set `OPENALEX_MAILTO=you@example.com` for the best reliability.

## Features
- Sources: **OpenAlex** (reconstructed abstracts) + **arXiv** (preprints).  
- Optional **Crossref** for DOI coverage.  
- Output: `results/<topic-slug>/papers/*.json` + `index.jsonl`.  
- Relevance: keyword-overlap baseline + optional **Ollama** classifier (0..1 score).  
- Dedup: DOI → arXiv ID → OpenAlex ID → title hash.

## Quickstart
```bash
python3 -m venv .venv
. ./.venv/bin/activate
pip install -r requirements.txt

# recommend identifying yourself to OpenAlex:
export OPENALEX_MAILTO="you@example.com"

# optional: run a local model for reranking
ollama pull llama3.1:8b
ollama run llama3.1:8b

# run a search
python cli.py "diffusion models for medical imaging" \
  --years 2022-2025 --per-source 50 \
  --min-score 0.2 \
  --outdir results
